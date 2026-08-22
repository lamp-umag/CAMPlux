"""
El Espejo de Malleco — elespejodemalleco.cl
Angol-based, covers Malleco province. robots.txt: 404s (no robots.txt file
present) -- no disallow found, same "404 = no disallow" precedent as
iquiquealdia. WP REST API confirmed live 2026-08-22: oldest indexed post
2019-11-25, newest same-day as check, X-WP-Total 1151. per_page=100 + full
_embed/_fields timed ~4.1s -- no override needed.
"""
from .wordpress import WordPressScraper


class ElEspejoDeMallecoScraper(WordPressScraper):
    name = "El Espejo de Malleco"
    base_url = "https://elespejodemalleco.cl"
    region = "araucania"
    min_delay = 1.0
