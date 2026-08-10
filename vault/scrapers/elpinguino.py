"""
El Pingüino — elpinguino.com

Discovery: Internal JSON API GET /v2/home/search/{YYYY-MM-DD}
  → returns all articles for a date with title, excerpt, category, slug.
  No text-search endpoint exists — only day-by-day iteration.

Search mode optimisation (parallel discovery):
  Daily API calls are tiny JSON (~1 KB). No crawl-delay in robots.txt.
  In search mode we fan out up to DISCOVERY_WORKERS concurrent threads at
  DISCOVERY_DELAY seconds each. Wall-clock for 6000 days drops from ~100 min
  to ~3 min. Article page fetches (heavier HTML) stay sequential at 1 s.

Bulk mode: sequential at the user-set delay (full pages for every article).

Full body: GET /noticia/{YYYY}/{MM}/{DD}/{slug}
  → single-article page, body in .sit3-single-body (their CSS typo, not ours).

Encoding: server mis-declares UTF-8; pass r.content to lxml to read <meta charset>.
"""
import re
import queue
import threading
import time
import logging
import concurrent.futures as cf
from datetime import date, timedelta
from bs4 import BeautifulSoup

import requests

from .base import BaseScraper, HEADERS

logger = logging.getLogger(__name__)

DATE_API = "https://elpinguino.com/v2/home/search"
BASE     = "https://www.elpinguino.com"

DISCOVERY_WORKERS = 10
DISCOVERY_DELAY   = 0.3


def build_url(item, date_str):
    """
    Correct URL for an El Pingüino article.
    Before 2014-04-01: /noticias/{ID}  (slug is empty, ID field present)
    After  2014-04-01: /noticia/YYYY/MM/DD/{slug}
    """
    slug = item.get("post_slug", "")
    if slug:
        yyyy, mm, dd = date_str[:4], date_str[5:7], date_str[8:10]
        return f"{BASE}/noticia/{yyyy}/{mm}/{dd}/{slug}"
    else:
        aid = item.get("ID", item.get("id", ""))
        if aid:
            return f"{BASE}/noticias/{aid}"
        return f"{BASE}/noticias/unknown-{date_str}-{item.get('post_title','')[:20]}"


def iter_dates(date_from, date_to):
    try:
        d   = date.fromisoformat(date_from)
        end = date.fromisoformat(date_to)
    except (ValueError, TypeError):
        return
    while d <= end:
        yield d.isoformat()
        d += timedelta(days=1)


class ElPinguinoScraper(BaseScraper):
    name      = "El Pingüino"
    base_url  = BASE
    min_delay = 1.0
    # Bounded concurrency for bulk-mode per-article fetches. Measured with
    # deploy/elpinguino_worker_test.py on 2026-08-10 (20 real article URLs,
    # same success rate at every level tested):
    #   workers=1  0.64 articles/s   workers=3  1.72/s
    #   workers=5  2.76/s (chosen)   workers=8  3.55/s
    # 5 is a solid ~4.3x speedup without pushing to the most aggressive
    # setting tested -- this site is Cloudflare-fronted and we depend on it
    # long-term, no reason to lean on the ceiling.
    BULK_WORKERS = 5

    # ------------------------------------------------------------------ date API (single)

    def _fetch_day_raw(self, session, date_str, delay=DISCOVERY_DELAY):
        """Fetch one date via a provided requests.Session (thread-safe call)."""
        time.sleep(delay)
        try:
            r = session.get(f"{DATE_API}/{date_str}", timeout=15)
            if r.status_code != 200:
                return date_str, []
            data = r.json()
            if data.get("info", {}).get("api_code") == 404:
                return date_str, []
            return date_str, data.get("result", [])
        except Exception as e:
            logger.warning("EP date API failed %s: %s", date_str, e)
            return date_str, []

    # ------------------------------------------------------------------ parallel discovery

    def _discover_parallel(self, date_from, date_to, query_lower, log_q):
        """
        Fan out date API calls across DISCOVERY_WORKERS threads.
        Returns a list of (date_str, item) tuples for articles passing the query filter.
        Items are in chronological order.
        """
        all_dates = list(iter_dates(date_from, date_to))
        total     = len(all_dates)
        log_q.put(f"Discovery: {total} days to scan ({DISCOVERY_WORKERS} parallel workers)")

        results   = {}   # date_str → [items]
        lock      = threading.Lock()
        idx       = [0]  # shared counter protected by lock

        def worker():
            # Each worker gets its own session so connections don't share state
            session = requests.Session()
            session.headers.update(HEADERS)
            while True:
                with lock:
                    if idx[0] >= total:
                        return
                    date_str = all_dates[idx[0]]
                    idx[0] += 1
                d, items = self._fetch_day_raw(session, date_str)
                with lock:
                    results[d] = items

        threads = [threading.Thread(target=worker, daemon=True)
                   for _ in range(DISCOVERY_WORKERS)]
        for t in threads:
            t.start()

        # Report progress while threads run
        done_last = 0
        while any(t.is_alive() for t in threads):
            time.sleep(2)
            with lock:
                done = len(results)
            if done != done_last:
                log_q.put(f"  Discovery: {done}/{total} days scanned…")
                done_last = done

        for t in threads:
            t.join()

        # Reassemble in chronological order and apply query filter
        matches = []
        for date_str in all_dates:
            for item in results.get(date_str, []):
                if query_lower:
                    haystack = f"{item.get('post_title','')} {item.get('post_excerpt','')}".lower()
                    if query_lower not in haystack:
                        continue
                matches.append((date_str, item))

        log_q.put(f"Discovery done — {len(matches)} candidate articles from {total} days")
        return matches

    # ------------------------------------------------------------------ article page

    # Real bug found 2026-08-07: El Pingüino sits behind Cloudflare. When it
    # serves a rate-limit/bot-challenge page, that response is still HTTP 200
    # (so self.get()'s retry-on-network-error never triggers), the CSS
    # selectors below simply find nothing on the challenge page, and the old
    # code silently fell back to the API's ~10-word excerpt with no error
    # logged anywhere -- affected 57% of the archive by the time anyone
    # noticed (worse over time, presumably as Cloudflare protection tightened
    # or scrape volume grew). Fixed by detecting a degraded response
    # (challenge-page markers, or a suspiciously short body after a normal
    # parse) and actually retrying instead of accepting it.
    _CHALLENGE_MARKERS = (
        "Just a moment", "cf-browser-verification", "Attention Required",
        "cf-chl", "Enable JavaScript and cookies", "Checking your browser",
    )
    _MIN_PLAUSIBLE_BODY_CHARS = 150

    def _fetch_body(self, url, delay, retries=3):
        last_result = None
        for attempt in range(retries):
            result = self._fetch_body_once(url, delay if attempt == 0 else delay * 2)
            if result is None:
                continue  # network-level failure -- try again
            _title, _date, _section, body_text, _image = result
            looks_ok = len(body_text) >= self._MIN_PLAUSIBLE_BODY_CHARS
            if looks_ok:
                return result
            last_result = result
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))  # back off before retrying
        # Ran out of retries. A genuine (if short) article body is still
        # better than the caller's API-excerpt fallback -- keep it. But a
        # real challenge-page hit leaves body_text empty (see
        # _fetch_body_once), and an empty result here should fall through to
        # that fallback rather than overwrite it with nothing.
        if last_result and last_result[3]:
            return last_result
        return None

    def _fetch_body_once(self, url, delay):
        r = self.get(url, delay=delay)
        if not r:
            return None

        if any(marker in r.text for marker in self._CHALLENGE_MARKERS):
            return "", "", "", "", ""  # looks_ok will be False -> triggers retry

        soup = BeautifulSoup(r.content, "lxml")

        # Title — h1 works on both old and new templates
        title_el = soup.select_one(".site3-single h1") or soup.select_one("h1")
        title    = title_el.get_text(strip=True) if title_el else ""

        # Section / category
        cat_el  = soup.select_one(".meta.cat")
        section = cat_el.get_text(strip=True) if cat_el else ""
        if not section:
            # Old template: first .meta sibling is usually the category
            metas = soup.select(".meta")
            if metas:
                section = metas[0].get_text(strip=True)

        # Date — extract from meta strings like "08/01/2009 a las 12:15"
        date_str = ""
        for el in soup.select(".site3-meta-title .meta") + soup.select(".meta"):
            text = el.get_text(" ", strip=True)
            m = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
            if m:
                date_str = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                break

        # Body — try new template first, fall back to old template
        #   New (post-2014 with slug): .sit3-single-body
        #   Old (pre-2014, /noticias/{id}): .post-body
        body_el = (soup.select_one(".sit3-single-body")
                   or soup.select_one(".post-body"))
        body_text = ""
        if body_el:
            for tag in body_el(["script", "style"]):
                tag.decompose()
            # Old template: text may sit directly in the container or in <p>/<br> separated chunks
            paragraphs = [p.get_text(" ", strip=True)
                          for p in body_el.find_all("p")
                          if p.get_text(strip=True)]
            if paragraphs:
                body_text = " ".join(paragraphs)
            else:
                # No <p> tags — old articles sometimes use raw text + <br>
                body_text = body_el.get_text(" ", strip=True)

        # Image URL — og:image first (covers new articles cleanly),
        # fall back to first content image in the body for old articles.
        image_url = ""
        og = soup.select_one('meta[property="og:image"]')
        if og and og.get("content"):
            image_url = og["content"]
        elif body_el:
            for im in body_el.select("img"):
                src = im.get("src") or im.get("data-src") or ""
                if src and "logo" not in src.lower():
                    image_url = src
                    break
        # Normalise protocol-relative URLs (//elpinguino.com/...)
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        elif image_url.startswith("/"):
            image_url = BASE + image_url

        return title, date_str, section, body_text, image_url

    # ------------------------------------------------------------------ run

    def run(self, query="", date_from="", date_to="", delay=1.5):
        if not date_from or not date_to:
            yield {"type": "log", "level": "warn",
                   "msg": "El Pingüino requires a date range — use From / To fields"}
            return

        query_lower    = query.lower().strip()
        is_search_mode = bool(query_lower)

        # ---------- SEARCH MODE: parallel discovery, then fetch only matches ----------
        if is_search_mode:
            log_q = queue.Queue()
            # Run parallel discovery in a background thread so we can yield logs
            candidates = [None]
            def run_discovery():
                candidates[0] = self._discover_parallel(
                    date_from, date_to, query_lower, log_q)

            disc_thread = threading.Thread(target=run_discovery, daemon=True)
            disc_thread.start()

            while disc_thread.is_alive() or not log_q.empty():
                try:
                    msg = log_q.get(timeout=0.5)
                    yield {"type": "log", "level": "info", "msg": msg}
                except queue.Empty:
                    pass
            disc_thread.join()

            total_articles = 0
            for date_str, item in (candidates[0] or []):
                api_title  = item.get("post_title", "")
                api_excerpt = item.get("post_excerpt", "")
                url = build_url(item, date_str)

                result = self._fetch_body(url, delay=max(delay, self.min_delay))
                if result:
                    title, art_date, section, body_text, image_url = result
                else:
                    title, art_date, section, body_text, image_url = (
                        api_title, date_str, item.get("post_category", ""),
                        api_excerpt, "")

                yield {
                    "type": "article",
                    "data": {
                        "source":    "El Pingüino",
                        "date":      art_date or date_str,
                        "title":     title or api_title,
                        "url":       url,
                        "body_text": body_text or api_excerpt,
                        "section":   section or item.get("post_category", ""),
                        "image_url": image_url,
                    },
                }
                total_articles += 1

            yield {"type": "log", "level": "info",
                   "msg": f"Done — {total_articles} articles collected"}

        # ---------- BULK MODE: sequential day discovery, bounded-concurrent article fetch ----------
        # Day-by-day date-API calls stay sequential (cheap, ~1KB JSON each).
        # Per-article page fetches (the actual bottleneck -- at min_delay=1.5s
        # sequential, a multi-year range is tens of hours of pure delay) run
        # through a small bounded thread pool instead. BULK_WORKERS was
        # chosen from an actual measured comparison, not guessed -- see
        # deploy/elpinguino_worker_test.py and its logged results.
        else:
            total_days, total_articles = 0, 0
            with cf.ThreadPoolExecutor(max_workers=self.BULK_WORKERS) as pool:
                for date_str in iter_dates(date_from, date_to):
                    total_days += 1
                    _, items = self._fetch_day_raw(self.session, date_str, delay=max(delay, self.min_delay))

                    if items:
                        def fetch_one(item, date_str=date_str):
                            url = build_url(item, date_str)
                            return item, url, self._fetch_body(url, delay=max(delay, self.min_delay))

                        futures = [pool.submit(fetch_one, item) for item in items]
                        for fut in cf.as_completed(futures):
                            item, url, result = fut.result()
                            api_title   = item.get("post_title", "")
                            api_excerpt = item.get("post_excerpt", "")
                            if result:
                                title, art_date, section, body_text, image_url = result
                            else:
                                title, art_date, section, body_text, image_url = (
                                    api_title, date_str, item.get("post_category", ""),
                                    api_excerpt, "")

                            yield {
                                "type": "article",
                                "data": {
                                    "source":    "El Pingüino",
                                    "date":      art_date or date_str,
                                    "title":     title or api_title,
                                    "url":       url,
                                    "body_text": body_text or api_excerpt,
                                    "section":   section or item.get("post_category", ""),
                                    "image_url": image_url,
                                },
                            }
                            total_articles += 1

                    if total_days % 10 == 0:
                        yield {"type": "log", "level": "info",
                               "msg": f"  {total_days} days, {total_articles} articles so far"}

            yield {"type": "log", "level": "info",
                   "msg": f"Done — {total_days} days scanned, {total_articles} articles collected"}
