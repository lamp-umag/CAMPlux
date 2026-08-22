"""
Malleco 7 — malleco7.cl
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2019-05-05, newest same-day as check,
X-WP-Total 4699. per_page=100 + full _embed/_fields timed ~3.9s -- no
override needed.
"""
from .wordpress import WordPressScraper


class Malleco7Scraper(WordPressScraper):
    name = "Malleco 7"
    base_url = "https://www.malleco7.cl"
    region = "araucania"
    min_delay = 1.0
