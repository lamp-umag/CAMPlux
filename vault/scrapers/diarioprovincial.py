"""
Diario Provincial — diarioprovincial.cl
Arauco province news. robots.txt: no crawl-delay/disallow on wp-json. WP
REST API confirmed live 2026-08-22: oldest indexed post 2020-06-03, newest
2026-08-19, X-WP-Total 2276. per_page=100 + full _embed/_fields timed
~7.4s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioProvincialScraper(WordPressScraper):
    name = "Diario Provincial"
    base_url = "https://diarioprovincial.cl"
    region = "biobio"
    min_delay = 1.0
