"""
Crónica Noticias — cronicanoticias.cl
Curicó province digital-native outlet, active recent posts. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2024-01-03, newest 2026-08-20, X-WP-Total 1712.
per_page=100 + full _embed/_fields timed ~1.5s -- no override needed.
"""
from .wordpress import WordPressScraper


class CronicaNoticiasScraper(WordPressScraper):
    name = "Crónica Noticias"
    base_url = "https://cronicanoticias.cl"
    region = "maule"
    min_delay = 1.0
