from .wordpress import WordPressScraper

class ElDinamoScraper(WordPressScraper):
    name           = "El Dínamo"
    base_url       = "https://www.eldinamo.cl"
    region         = "nacional"
    min_delay      = 1.0
    use_browser_ua = True
