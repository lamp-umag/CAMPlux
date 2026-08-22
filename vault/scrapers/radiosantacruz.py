"""
Radio Santa Cruz — santacruzfm.cl
Has a dedicated /noticias/ section on-site too. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2021-10-08, newest same-day as check, X-WP-Total 2139.
per_page=100 + full _embed/_fields timed ~6.2s -- no override needed.
"""
from .wordpress import WordPressScraper


class RadioSantaCruzScraper(WordPressScraper):
    name = "Radio Santa Cruz"
    base_url = "https://santacruzfm.cl"
    region = "ohiggins"
    min_delay = 1.0
