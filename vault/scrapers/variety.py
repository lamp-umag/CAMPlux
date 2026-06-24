from .wordpress import WordPressScraper

class VarietyScraper(WordPressScraper):
    name           = "Variety"
    base_url       = "https://variety.com"
    region         = "internacional"
    min_delay      = 1.0
    use_browser_ua = True
