from .sitemap import SitemapScraper


class TheGuardianScraper(SitemapScraper):
    """
    The Guardian (UK) — single rolling news sitemap (last ~48h only). Historical
    archive isn't exposed via sitemaps. URLs contain /YYYY/mon/DD/ where 'mon'
    is the lowercase English month abbreviation.
    """
    name           = "The Guardian"
    base_url       = "https://www.theguardian.com"
    region         = "internacional"
    min_delay      = 1.0
    body_selector  = '[data-gu-name="body"]'
    date_meta_prop = "article:published_time"

    def iter_sitemap_urls(self, date_from, date_to):
        yield f"{self.base_url}/sitemaps/news.xml"

    _MONTHS = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }

    def _date_from_url(self, url):
        import re
        m = re.search(r"/(\d{4})/([a-z]{3})/(\d{1,2})/", url)
        if not m:
            return ""
        mm = self._MONTHS.get(m.group(2))
        if not mm:
            return ""
        return f"{m.group(1)}-{mm}-{int(m.group(3)):02d}"
