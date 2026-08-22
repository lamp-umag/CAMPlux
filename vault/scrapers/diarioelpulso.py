"""
Diario El Pulso — diarioelpulso.cl
Also runs "Radio El Pulso" online. robots.txt: no crawl-delay/disallow on
wp-json. WP REST API confirmed live 2026-08-22: oldest indexed post
2019-09-01, newest same-day as check, X-WP-Total 18089. per_page=100 +
full _embed/_fields timed ~4.2s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioElPulsoScraper(WordPressScraper):
    name = "Diario El Pulso"
    base_url = "https://www.diarioelpulso.cl"
    region = "ohiggins"
    min_delay = 1.0
