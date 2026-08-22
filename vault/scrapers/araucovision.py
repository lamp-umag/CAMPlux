"""
Araucovisión — araucovision.cl
Arauco province news portal, TV-adjacent. robots.txt: no crawl-delay/
disallow on wp-json. WP REST API confirmed live 2026-08-22: oldest indexed
post 2025-03-05, newest 2026-08-14, X-WP-Total 113 (small but active
archive). per_page=100 + full _embed/_fields timed ~3.7s -- no override
needed.
"""
from .wordpress import WordPressScraper


class AraucovisionScraper(WordPressScraper):
    name = "Araucovisión"
    base_url = "https://araucovision.cl"
    region = "biobio"
    min_delay = 1.0
