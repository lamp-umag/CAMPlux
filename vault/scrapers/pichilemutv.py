"""
PichilemuTV — pichilemutv.org
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2008-04-29, newest same-day as check,
X-WP-Total 2618. per_page=100 + full _embed/_fields timed ~4.4s -- no
override needed.
"""
from .wordpress import WordPressScraper


class PichilemuTvScraper(WordPressScraper):
    name = "PichilemuTV"
    base_url = "https://pichilemutv.org"
    region = "ohiggins"
    min_delay = 1.0
