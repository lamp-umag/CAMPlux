"""
El Aconcagua — elaconcagua.cl
San Felipe / Aconcagua valley. Bare domain 301-redirects to www --
base_url set directly to the www host to avoid the extra hop. robots.txt
(on www.elaconcagua.cl) has "Crawl-delay: 10" -- min_delay set
accordingly, same treatment as Ovalle Hoy / HDN Digital precedents. WP
REST API confirmed live 2026-08-22: oldest indexed post 2016-01-04, newest
2026-08-21, X-WP-Total 7515. per_page=100 + full _embed/_fields timed
~14.2s -- within budget, no per_page override needed on top of the
Crawl-delay.
"""
from .wordpress import WordPressScraper


class ElAconcaguaScraper(WordPressScraper):
    name = "El Aconcagua"
    base_url = "https://www.elaconcagua.cl"
    region = "valparaiso"
    min_delay = 10.0
