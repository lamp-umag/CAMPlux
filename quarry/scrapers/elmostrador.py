from .sitemap import SitemapScraper

class ElMostradorScraper(SitemapScraper):
    name           = "El Mostrador"
    base_url       = "https://www.elmostrador.cl"
    region         = "nacional"
    min_delay      = 1.0
    body_selector  = "div.d-the-single__text"
    date_meta_prop = None  # No published-time meta; URL contains YYYY/MM/DD

    def iter_sitemap_urls(self, date_from, date_to):
        # El Mostrador exposes only one rolling sitemap covering recent weeks.
        # Historical content is not reachable via sitemaps.
        yield f"{self.base_url}/sitemap.xml"
