"""
Ñuble Actual — www.nubleactual.cl
robots.txt: standard Disallow: /wp-admin/ only -- no crawl-delay, no wp-json
disallow. WP REST API confirmed live 2026-08-22: oldest indexed post
2023-10-30, newest 2026-08-21, X-WP-Total 13257 (largest of the Ñuble
outlets). per_page=100 + full _embed/_fields timed ~2.1s -- no override
needed.
"""
from .wordpress import WordPressScraper


class NubleActualScraper(WordPressScraper):
    name = "Ñuble Actual"
    base_url = "https://www.nubleactual.cl"
    region = "nuble"
    min_delay = 1.0
