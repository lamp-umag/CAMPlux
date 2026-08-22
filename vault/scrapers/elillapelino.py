"""
El Illapelino — www.elillapelino.cl
"Diario Electrónico de Illapel", covers Choapa province. robots.txt: no
crawl-delay, no wp-json disallow. WP REST API confirmed live 2026-08-22:
oldest indexed post 2020-11-02, newest 2026-08-20, X-WP-Total 1377.
per_page=100 + full _embed/_fields timed ~3.6s -- no override needed.
"""
from .wordpress import WordPressScraper


class ElIllapelinoScraper(WordPressScraper):
    name = "El Illapelino"
    base_url = "https://www.elillapelino.cl"
    region = "coquimbo"
    min_delay = 1.0
