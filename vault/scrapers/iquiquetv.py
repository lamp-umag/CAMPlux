"""
Iquique TV — iquiquetv.cl
Digital TV channel (2 TVD signals + VTR carriage) running a WP-based news
site. robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class IquiqueTvScraper(WordPressScraper):
    name = "Iquique TV"
    base_url = "https://iquiquetv.cl"
    region = "tarapaca"
    min_delay = 1.0
