"""
Tribuna Colchagua — latribunadecolchagua.cl
Covers Colchagua province (San Fernando, Santa Cruz, etc.). robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2023-01-04, newest same-day as check, X-WP-Total 994.
per_page=100 + full _embed/_fields timed ~3.8s -- no override needed.
"""
from .wordpress import WordPressScraper


class TribunaColchaguaScraper(WordPressScraper):
    name = "Tribuna Colchagua"
    base_url = "https://www.latribunadecolchagua.cl"
    region = "ohiggins"
    min_delay = 1.0
