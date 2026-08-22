"""
Las Noticias de Malleco — lasnoticiasdemalleco.cl
Claims to be the oldest continuously-published written outlet in the
Araucanía region. robots.txt: no crawl-delay/disallow on wp-json. WP REST
API confirmed live 2026-08-22: oldest indexed post 2022-07-20, newest
same-day as check, X-WP-Total 7636. per_page=100 + full _embed/_fields
timed ~5.7s -- no override needed.
"""
from .wordpress import WordPressScraper


class LasNoticiasDeMallecoScraper(WordPressScraper):
    name = "Las Noticias de Malleco"
    base_url = "https://lasnoticiasdemalleco.cl"
    region = "araucania"
    min_delay = 1.0
