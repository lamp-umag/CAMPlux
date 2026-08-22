"""
Diario El Centro — diarioelcentro.cl
Covers Talca, Curicó, and the wider Maule region. Bare domain 301-redirects
to www -- base_url set to the www host directly to avoid the extra hop.
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2022-02-25, newest same-day as check,
X-WP-Total 17520. per_page=100 + full _embed/_fields timed ~2.9s -- no
override needed.
"""
from .wordpress import WordPressScraper


class DiarioElCentroScraper(WordPressScraper):
    name = "Diario El Centro"
    base_url = "https://www.diarioelcentro.cl"
    region = "maule"
    min_delay = 1.0
