import re
from .sitemap import SitemapScraper

JSONLD_DATE_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"')


class CnnChileScraper(SitemapScraper):
    """
    CNN Chile monthly sitemaps at /_files/sitemaps/YYYY/MM.xml.
    Article dates aren't in meta tags — only in JSON-LD inside <script>.
    """
    name           = "CNN Chile"
    base_url       = "https://www.cnnchile.com"
    region         = "nacional"
    min_delay      = 1.0
    body_selector  = "article.main-article"
    date_meta_prop = None

    def monthly_sitemap_url(self, year, month):
        return f"{self.base_url}/_files/sitemaps/{year}/{month:02d}.xml"

    def parse_article(self, html, url, fallback_date):
        data = super().parse_article(html, url, fallback_date)
        # Override date: extract from JSON-LD datePublished
        m = JSONLD_DATE_RE.search(html)
        if m:
            data["date"] = m.group(1)[:10]
        elif not data["date"]:
            data["date"] = fallback_date[:10]
        return data
