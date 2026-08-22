"""
Linares en Línea — linaresenlinea.cl
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2016-09-19, newest same-day as check,
X-WP-Total 19776. per_page=100 + full _embed/_fields timed ~2.4s -- no
override needed.
"""
from .wordpress import WordPressScraper


class LinaresEnLineaScraper(WordPressScraper):
    name = "Linares en Línea"
    base_url = "https://linaresenlinea.cl"
    region = "maule"
    min_delay = 1.0
