"""
Generic sitemap-based scraper for sites without WP REST API.

Subclasses provide:
  - monthly_sitemap_url(year, month) → URL of monthly sitemap (or None)
    OR override iter_sitemap_urls() for non-monthly patterns
  - body_selector — CSS selector for the article body element
  - date_meta_prop — meta property holding the published date (or None to use URL)
"""
import re
import datetime
from html import unescape
from bs4 import BeautifulSoup

from .base import BaseScraper

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class SitemapScraper(BaseScraper):
    name = "Sitemap Site"
    base_url = ""
    min_delay = 1.0
    use_browser_ua = True

    body_selector = "article"
    date_meta_prop = "article:published_time"  # set to None to use URL date

    def __init__(self):
        super().__init__()
        if self.use_browser_ua:
            self.session.headers["User-Agent"] = BROWSER_UA

    # ── sitemap discovery (subclass hooks) ───────────────────────────────────

    def monthly_sitemap_url(self, year, month):
        """Return URL of the sitemap for the given month, or None."""
        return None

    def iter_sitemap_urls(self, date_from, date_to):
        """Yield all sitemap URLs that may cover the date range."""
        for y, m in self._months_in_range(date_from, date_to):
            url = self.monthly_sitemap_url(y, m)
            if url:
                yield url

    def _months_in_range(self, date_from, date_to):
        df = datetime.date.fromisoformat(date_from[:10])
        dt = datetime.date.fromisoformat(date_to[:10])
        y, m = df.year, df.month
        end = (dt.year, dt.month)
        while (y, m) <= end:
            yield y, m
            m += 1
            if m > 12:
                m, y = 1, y + 1

    def _iter_urls_in_sitemap(self, sitemap_url, delay):
        r = self.get(sitemap_url, delay=delay)
        if not r:
            return
        soup = BeautifulSoup(r.content, "xml")
        for url_el in soup.find_all("url"):
            loc = url_el.find("loc")
            if not loc:
                continue
            lastmod = url_el.find("lastmod")
            yield loc.get_text(strip=True), (lastmod.get_text(strip=True) if lastmod else "")

    # ── article parsing ──────────────────────────────────────────────────────

    def parse_article(self, html, url, fallback_date):
        soup = BeautifulSoup(html, "lxml")

        title = ""
        ogt = soup.find("meta", {"property": "og:title"})
        if ogt and ogt.get("content"):
            title = unescape(ogt["content"]).strip()
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

        date = ""
        if self.date_meta_prop:
            meta = soup.find("meta", {"property": self.date_meta_prop})
            if meta and meta.get("content"):
                date = meta["content"][:10]
        if not date:
            date = self._date_from_url(url) or fallback_date[:10]

        body_text = ""
        el = soup.select_one(self.body_selector)
        if el:
            body_text = self.clean_html(el)

        image_url = ""
        ogi = soup.find("meta", {"property": "og:image"})
        if ogi and ogi.get("content"):
            image_url = ogi["content"]

        excerpt = ""
        ogd = soup.find("meta", {"property": "og:description"})
        if ogd and ogd.get("content"):
            excerpt = ogd["content"]

        return {
            "title":     title,
            "body_text": body_text,
            "date":      date,
            "image_url": image_url,
            "excerpt":   excerpt,
            "section":   self._section_from_url(url),
        }

    def _date_from_url(self, url):
        m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""

    def _section_from_url(self, url):
        m = re.search(r"://[^/]+/([^/]+)/", url)
        return m.group(1) if m else ""

    # ── main loop ────────────────────────────────────────────────────────────

    def run(self, query="", date_from="", date_to="", delay=1.5):
        actual_delay = max(delay, self.min_delay)
        if not date_from or not date_to:
            yield {"type": "log", "level": "error", "msg": "date_from y date_to son obligatorios"}
            return

        df = date_from[:10]
        dt = date_to[:10]

        seen = set()
        all_articles = []  # list of (url, fallback_date)

        for sm_url in self.iter_sitemap_urls(date_from, date_to):
            yield {"type": "log", "level": "info", "msg": f"  sitemap → {sm_url}"}
            n_added = 0
            for url, lastmod in self._iter_urls_in_sitemap(sm_url, actual_delay):
                if url in seen:
                    continue
                seen.add(url)
                # Pre-filter: if we can confidently date the URL via lastmod or
                # URL path, drop ones outside range. Otherwise pass through and
                # filter post-fetch using the parsed article date.
                url_date = self._date_from_url(url)
                if url_date:
                    if url_date < df or url_date > dt:
                        continue
                # Without a URL date we can't pre-filter reliably (lastmod may be
                # bulk-rewritten as on CNN Chile); accept and check post-fetch.
                all_articles.append((url, lastmod or url_date))
                n_added += 1
            yield {"type": "log", "level": "info", "msg": f"    +{n_added} URLs"}

        yield {
            "type": "log", "level": "info",
            "msg": f"Total: {len(all_articles)} URLs a descargar"
        }
        yield {"type": "total", "n": len(all_articles)}

        for url, fallback_date in all_articles:
            r = self.get(url, delay=actual_delay)
            if not r:
                yield {"type": "fail", "url": url}
                continue
            # Many Chilean sites send pages without a charset header — requests
            # falls back to ISO-8859-1 and mangles accents. Force UTF-8.
            if not r.encoding or r.encoding.lower() in ("iso-8859-1", "latin-1"):
                r.encoding = "utf-8"
            try:
                data = self.parse_article(r.text, url, fallback_date)
            except Exception as e:
                yield {"type": "log", "level": "warn", "msg": f"  parse error en {url}: {e}"}
                continue
            if not data["body_text"] or len(data["body_text"]) < 100:
                continue
            # Post-fetch date filter (catches URLs we couldn't pre-filter)
            if data["date"] and (data["date"] < df or data["date"] > dt):
                continue
            data["source"] = self.name
            data["url"] = url
            yield {"type": "article", "data": data}
