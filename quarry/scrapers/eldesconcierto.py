from .wordpress import WordPressScraper

class ElDesconciertoScraper(WordPressScraper):
    name           = "El Desconcierto"
    base_url       = "https://www.eldesconcierto.cl"
    region         = "nacional"
    min_delay      = 1.0
    use_browser_ua = True
    enabled        = False
    note           = "Sin WP REST API. Pendiente scraper sitemap."
