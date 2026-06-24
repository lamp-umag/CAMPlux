import datetime
from .sitemap import SitemapScraper

class BioBioChileScraper(SitemapScraper):
    """
    BioBioChile uses month-offset sitemaps: sitemap-YYYY-MM.xml is generated
    at the START of YYYY-MM and contains articles from the PRIOR month.
    The current month (no rolled-over sitemap yet) lives in news-sitemap.xml.
    """
    name           = "BioBioChile"
    base_url       = "https://www.biobiochile.cl"
    region         = "nacional"
    min_delay      = 1.0
    body_selector  = "div.post-content"
    date_meta_prop = "article:published_time"

    def iter_sitemap_urls(self, date_from, date_to):
        df = datetime.date.fromisoformat(date_from[:10])
        dt = datetime.date.fromisoformat(date_to[:10])
        today = datetime.date.today()
        current_month = (today.year, today.month)
        seen = set()
        # For each month in range, fetch the NEXT month's sitemap.
        y, m = df.year, df.month
        while (y, m) <= (dt.year, dt.month):
            if (y, m) == current_month:
                # No rolled-over sitemap yet → use news-sitemap.xml
                url = f"{self.base_url}/news-sitemap.xml"
            else:
                ny, nm = (y, m + 1) if m < 12 else (y + 1, 1)
                url = f"{self.base_url}/static/sitemap-{ny}-{nm:02d}.xml"
            if url not in seen:
                seen.add(url)
                yield url
            m += 1
            if m > 12:
                m, y = 1, y + 1
