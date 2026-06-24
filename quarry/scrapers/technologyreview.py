from .wordpress import WordPressScraper

class TechnologyReviewScraper(WordPressScraper):
    name           = "MIT Technology Review"
    base_url       = "https://www.technologyreview.com"
    region         = "internacional"
    min_delay      = 1.0
    use_browser_ua = True
