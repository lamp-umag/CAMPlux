"""
Diario Puerto Varas — diariopuertovaras.cl
Self-described community-focused digital outlet. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2017-10-18, newest same-day as check, X-WP-Total 7622.
per_page=100 + full _embed/_fields timed ~4.9s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioPuertoVarasScraper(WordPressScraper):
    name = "Diario Puerto Varas"
    base_url = "https://diariopuertovaras.cl"
    region = "los_lagos"
    min_delay = 1.0
