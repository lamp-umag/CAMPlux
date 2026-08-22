"""
El Proa (Proa Regional) — elproa.cl
San Antonio. robots.txt: no crawl-delay/disallow on wp-json. WP REST API
confirmed live 2026-08-22: oldest indexed post 2021-01-01, newest same-day
as check, X-WP-Total 18606. per_page=100 + full _embed/_fields timed
~1.4s -- no override needed.
"""
from .wordpress import WordPressScraper


class ElProaScraper(WordPressScraper):
    name = "El Proa"
    base_url = "https://elproa.cl"
    region = "valparaiso"
    min_delay = 1.0
