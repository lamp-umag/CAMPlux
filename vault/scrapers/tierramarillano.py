"""
Tierramarillano — tierramarillano.cl
robots.txt: sitemap-only, no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class TierramarillanoScraper(WordPressScraper):
    name = "Tierramarillano"
    base_url = "https://tierramarillano.cl"
    region = "atacama"
    min_delay = 1.0
