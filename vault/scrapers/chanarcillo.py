"""
Diario Chañarcillo — chanarcillo.cl
Self-described "único diario auténticamente regional." robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class ChanarcilloScraper(WordPressScraper):
    name = "Diario Chañarcillo"
    base_url = "https://www.chanarcillo.cl"
    region = "atacama"
    min_delay = 1.0
