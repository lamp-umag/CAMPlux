from .wordpress import WordPressScraper

class ElCiudadanoScraper(WordPressScraper):
    name           = "El Ciudadano"
    base_url       = "https://www.elciudadano.com"
    region         = "nacional"
    min_delay      = 1.5
    use_browser_ua = True
