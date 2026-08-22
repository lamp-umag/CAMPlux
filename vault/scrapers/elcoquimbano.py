"""
El Coquimbano — www.elcoquimbano.cl
One of Agencia Caracol's ~4 Coquimbo-region digital papers. robots.txt: no
crawl-delay, no wp-json disallow. WP REST API confirmed live 2026-08-22:
oldest indexed post 2020-08-20, newest 2026-08-21, X-WP-Total 4876.
per_page=100 + full _embed/_fields timed ~3.6s -- no override needed.
"""
from .wordpress import WordPressScraper


class ElCoquimbanoScraper(WordPressScraper):
    name = "El Coquimbano"
    base_url = "https://www.elcoquimbano.cl"
    region = "coquimbo"
    min_delay = 1.0
