"""
Angol Noticias — angolnoticiasnew.cl
Self-described main digital news outlet of Malleco province. robots.txt:
no crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2023-12-29, newest same-day as check, X-WP-Total 1620.
per_page=100 + full _embed/_fields timed ~3.9s -- no override needed.
"""
from .wordpress import WordPressScraper


class AngolNoticiasScraper(WordPressScraper):
    name = "Angol Noticias"
    base_url = "https://www.angolnoticiasnew.cl"
    region = "araucania"
    min_delay = 1.0
