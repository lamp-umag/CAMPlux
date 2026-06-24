from .wordpress import WordPressScraper

class ElLanquihueScraper(WordPressScraper):
    name           = "El Llanquihue"
    base_url       = "https://www.ellanquihue.cl"
    region         = "regional"
    min_delay      = 1.5
    use_browser_ua = True
    enabled        = False
    note           = "Sin WP REST API. Pendiente scraper sitemap."
