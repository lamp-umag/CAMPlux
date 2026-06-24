from .wordpress import WordPressScraper

class RollingStoneScraper(WordPressScraper):
    name           = "Rolling Stone"
    base_url       = "https://www.rollingstone.com"
    region         = "internacional"
    min_delay      = 1.0
    use_browser_ua = True
