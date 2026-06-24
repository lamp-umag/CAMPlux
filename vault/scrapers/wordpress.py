"""
Generic WordPress REST API scraper.
All WP-based sources inherit from WordPressScraper and set class-level constants.
"""
from html import unescape
import logging
from dateutil import parser as dateparser
from .base import BaseScraper

logger = logging.getLogger(__name__)

# _links is needed for _embed to follow; featured_media gives the image ID
FIELDS = "id,date,title,link,excerpt,content,categories,featured_media,_links"

# Browser-like UA for sites that block non-browser agents (e.g. itvpatagonia.com)
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class WordPressScraper(BaseScraper):
    """
    Scraper for any site with a public WordPress REST API at /wp-json/wp/v2/.

    Subclass and set:
        name           — display name
        base_url       — site root (no trailing slash)
        min_delay      — respects robots.txt Crawl-delay
        use_browser_ua — set True if the site blocks non-browser User-Agents
    """
    name = "WordPress Site"
    base_url = ""
    min_delay = 1.0
    use_browser_ua = False

    def __init__(self):
        super().__init__()
        if self.use_browser_ua:
            self.session.headers["User-Agent"] = BROWSER_UA

    @property
    def _api(self):
        return f"{self.base_url}/wp-json/wp/v2"

    def _fetch_categories(self, delay):
        cats = {}
        page = 1
        while True:
            r = self.get(f"{self._api}/categories?per_page=100&page={page}", delay=0.3)
            if not r:
                break
            data = r.json()
            if not data:
                break
            for c in data:
                cats[c["id"]] = c["name"]
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                break
            page += 1
        return cats

    def run(self, query="", date_from="", date_to="", delay=1.5):
        actual_delay = max(delay, self.min_delay)

        yield {"type": "log", "level": "info", "msg": "Fetching category index…"}
        categories = self._fetch_categories(actual_delay)

        params = {
            "per_page": 100,
            "_fields":  FIELDS,
            "_embed":   "wp:featuredmedia",
        }
        if query:
            params["search"] = query
        if date_from:
            try:
                params["after"] = (
                    dateparser.parse(date_from).replace(hour=0, minute=0, second=0).isoformat()
                )
            except Exception:
                pass
        if date_to:
            try:
                params["before"] = (
                    dateparser.parse(date_to).replace(hour=23, minute=59, second=59).isoformat()
                )
            except Exception:
                pass

        page         = 1
        total_pages  = None
        failed_pages = []

        while True:
            params["page"] = page
            r = self.get(f"{self._api}/posts", delay=actual_delay, params=params)

            if not r:
                failed_pages.append(page)
                status = getattr(self, "_last_status", 0)
                detail = f" HTTP {status}" if status else ""
                yield {
                    "type": "log", "level": "warn",
                    "msg": f"  ✗ page {page} failed{detail} — skipping, continuing…",
                }
                if total_pages is None:
                    # First page failed — we can't know how many pages exist; abort.
                    yield {"type": "log", "level": "error",
                           "msg": "  Abortando: primera página falló, no se puede continuar."}
                    break
                if page >= total_pages:
                    break
                page += 1
                continue

            # Guard against Cloudflare / redirect pages returning HTML with 200
            ct = r.headers.get("Content-Type", "")
            if "html" in ct and "json" not in ct:
                snippet = r.text[:160].strip().replace("\n", " ")
                yield {"type": "log", "level": "error",
                       "msg": f"  ✗ respuesta HTML, no JSON — ¿API deshabilitada o bloqueada? ({snippet[:80]}…)"}
                break

            try:
                posts = r.json()
            except ValueError:
                snippet = r.text[:160].strip().replace("\n", " ")
                yield {"type": "log", "level": "error",
                       "msg": f"  ✗ respuesta no JSON — ¿API deshabilitada? ({snippet[:80]}…)"}
                break

            if total_pages is None:
                total_pages = int(r.headers.get("X-WP-TotalPages", 1))
                total_posts = int(r.headers.get("X-WP-Total", 0))
                yield {
                    "type": "log", "level": "info",
                    "msg": f"{total_posts} posts across {total_pages} pages",
                }
                yield {"type": "total", "n": total_posts}

            if not posts:
                break

            for post in posts:
                cat_names = [categories.get(c, str(c)) for c in post.get("categories", [])]
                body_text = self.clean_html(post.get("content", {}).get("rendered", ""))
                title     = unescape(post.get("title", {}).get("rendered", ""))
                excerpt   = self.clean_html(post.get("excerpt", {}).get("rendered", ""))

                image_url = ""
                try:
                    media = post.get("_embedded", {}).get("wp:featuredmedia", [])
                    if media:
                        image_url = media[0].get("source_url", "")
                except Exception:
                    pass

                yield {
                    "type": "article",
                    "data": {
                        "source":    self.name,
                        "date":      post.get("date", "")[:10],
                        "title":     title,
                        "url":       post.get("link", ""),
                        "body_text": body_text,
                        "section":   ", ".join(cat_names),
                        "image_url": image_url,
                        "excerpt":   excerpt,
                    },
                }

            if page >= total_pages:
                break
            page += 1

        if failed_pages:
            yield {
                "type": "failed_pages",
                "pages": failed_pages,
                "msg": f"Skipped {len(failed_pages)} pages due to network errors: {failed_pages}",
            }
