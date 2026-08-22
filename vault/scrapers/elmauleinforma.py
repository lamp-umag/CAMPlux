"""
El Maule Informa — elmauleinforma.cl
Self-described independent/pluralist digital outlet based in Talca.
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2020-09-07, newest same-day as check,
X-WP-Total 23283. per_page=100 + full _embed/_fields timed ~4.0s -- no
override needed.
"""
from .wordpress import WordPressScraper


class ElMauleInformaScraper(WordPressScraper):
    name = "El Maule Informa"
    base_url = "https://elmauleinforma.cl"
    region = "maule"
    min_delay = 1.0
