"""
Quirihue Noticias — quirihuenoticias.cl
Quirihue / Ñuble province. robots.txt: standard Disallow: /wp-admin/ only --
no crawl-delay, no wp-json disallow. WP REST API confirmed live 2026-08-22:
oldest indexed post 2021-06-19, newest 2026-08-20, X-WP-Total 6332.
per_page=100 + full _embed/_fields timed ~3.6s -- no override needed.
"""
from .wordpress import WordPressScraper


class QuirihueNoticiasScraper(WordPressScraper):
    name = "Quirihue Noticias"
    base_url = "https://quirihuenoticias.cl"
    region = "nuble"
    min_delay = 1.0
