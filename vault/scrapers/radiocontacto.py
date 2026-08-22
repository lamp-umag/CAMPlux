"""
Radio Contacto 90.7 FM — radiocontacto.cl
Chillán/Ñuble news + music station. robots.txt: Yoast default block,
"Disallow:" (empty) -- no crawl-delay, no wp-json disallow. WP REST API
confirmed live 2026-08-22: oldest indexed post 2021-12-07, newest same-day
as this check, X-WP-Total 10636. per_page=100 + full _embed/_fields timed
~2.5s -- no override needed.
"""
from .wordpress import WordPressScraper


class RadioContactoScraper(WordPressScraper):
    name = "Radio Contacto 90.7 FM"
    base_url = "https://radiocontacto.cl"
    region = "nuble"
    min_delay = 1.0
