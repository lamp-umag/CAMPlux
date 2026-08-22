"""
Diario La Quinta — diariolaquinta.cl
Valparaíso -- noticias, opinión, cultura, eventos. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2018-03-08, newest same-day as check, X-WP-Total
16556. per_page=100 + full _embed/_fields timed ~6.6s -- no override
needed.
"""
from .wordpress import WordPressScraper


class DiarioLaQuintaScraper(WordPressScraper):
    name = "Diario La Quinta"
    base_url = "https://diariolaquinta.cl"
    region = "valparaiso"
    min_delay = 1.0
