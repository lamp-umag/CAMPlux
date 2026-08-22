"""
El Amanecer de lo Herrera — delh.cl
Maipo province: San Bernardo, Buin, Paine, Calera de Tango. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2019-09-03, newest same-day as check, X-WP-Total 3376.
per_page=100 + full _embed/_fields timed ~2.8s -- no per_page override
needed.
"""
from .wordpress import WordPressScraper


class DelhScraper(WordPressScraper):
    name = "El Amanecer de lo Herrera"
    base_url = "https://delh.cl"
    region = "metropolitana"
    min_delay = 1.0
