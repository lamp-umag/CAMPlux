from .wordpress import WordPressScraper

class TechCrunchScraper(WordPressScraper):
    name           = "TechCrunch"
    base_url       = "https://techcrunch.com"
    region         = "internacional"
    min_delay      = 1.0
    use_browser_ua = True
