"""
El Comunicador — elcomunicador.cl
Covers Melipilla, Talagante and Maipo provinces. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2025-01-02, newest 2026-08-21, X-WP-Total 482. Small
but real, actively updated archive. per_page=100 + full _embed/_fields
timed ~2.5s -- no per_page override needed.
"""
from .wordpress import WordPressScraper


class ElComunicadorScraper(WordPressScraper):
    name = "El Comunicador"
    base_url = "https://elcomunicador.cl"
    region = "metropolitana"
    min_delay = 1.0
