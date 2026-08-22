"""
Radio Riquelme — radioriquelme.cl
1350 AM, "Desde el Corazón de Coquimbo", covers La Serena/Coquimbo/rural
Elqui & Limarí. robots.txt: no crawl-delay, no wp-json disallow. WP REST
API confirmed live 2026-08-22: oldest indexed post 2019-01-29, newest
2026-08-21, X-WP-Total 14247. per_page=100 + full _embed/_fields timed
~5.0s -- no override needed.
"""
from .wordpress import WordPressScraper


class RadioRiquelmeScraper(WordPressScraper):
    name = "Radio Riquelme"
    base_url = "https://radioriquelme.cl"
    region = "coquimbo"
    min_delay = 1.0
