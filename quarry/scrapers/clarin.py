import re
import json
from bs4 import BeautifulSoup
from .sitemap import SitemapScraper


class ClarinScraper(SitemapScraper):
    """
    Clarín (Argentina) — sitemap index lists multiple chunks per month at
    /sitemaps/news-YYYY-MM-N.xml. Body lives in JSON-LD `articleBody`.
    """
    name           = "Clarín"
    base_url       = "https://www.clarin.com"
    region         = "internacional"
    min_delay      = 1.0
    date_meta_prop = "article:published_time"
    # body_selector unused — we override parse_article

    def iter_sitemap_urls(self, date_from, date_to):
        # Fetch the news index once and yield every monthly chunk in range.
        idx_url = f"{self.base_url}/sitemaps/index_news.xml"
        r = self.get(idx_url, delay=self.min_delay)
        if not r:
            return
        soup = BeautifulSoup(r.content, "xml")
        df = date_from[:7]   # YYYY-MM
        dt = date_to[:7]
        rx = re.compile(r"news-(\d{4})-(\d{2})-\d+\.xml")
        for sm in soup.find_all("sitemap"):
            loc = sm.find("loc")
            if not loc:
                continue
            url = loc.get_text(strip=True)
            m = rx.search(url)
            if not m:
                continue
            ym = f"{m.group(1)}-{m.group(2)}"
            if df <= ym <= dt:
                yield url

    def parse_article(self, html, url, fallback_date):
        data = super().parse_article(html, url, fallback_date)
        # Prefer JSON-LD articleBody when available (much cleaner than DOM)
        for raw in re.findall(r'<script[^>]+ld\+json[^>]*>(.+?)</script>',
                              html, re.DOTALL):
            try:
                d = json.loads(raw)
                if isinstance(d, list):
                    d = d[0] if d else {}
                t = d.get("@type")
                if isinstance(t, list):
                    t = t[0] if t else ""
                if t in ("NewsArticle", "Article", "Report"):
                    body = d.get("articleBody", "")
                    if body and len(body) > len(data.get("body_text", "")):
                        data["body_text"] = body
                    dp = d.get("datePublished", "")
                    if dp and not data.get("date"):
                        data["date"] = dp[:10]
                    break
            except Exception:
                continue
        return data
