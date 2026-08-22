"""
Araucanía Noticias — araucanianoticias.cl
Independent, Temuco-based, founded 2011. robots.txt: no crawl-delay/
disallow on wp-json. WP REST API confirmed live 2026-08-22: oldest indexed
post 2011-01-28, newest same-day as check, X-WP-Total 64734 (biggest
archive found across this region). per_page=100 + full _embed/_fields
timed ~3.5s -- no override needed.
"""
from .wordpress import WordPressScraper


class AraucaniaNoticiasScraper(WordPressScraper):
    name = "Araucanía Noticias"
    base_url = "https://araucanianoticias.cl"
    region = "araucania"
    min_delay = 1.0
