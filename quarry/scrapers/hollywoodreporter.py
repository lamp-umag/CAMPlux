from .wordpress import WordPressScraper

class HollywoodReporterScraper(WordPressScraper):
    name           = "The Hollywood Reporter"
    base_url       = "https://www.hollywoodreporter.com"
    region         = "internacional"
    min_delay      = 1.0
    use_browser_ua = True
