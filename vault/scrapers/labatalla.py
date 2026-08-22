"""
La Batalla de Maipú — www.labatalla.cl
Maipú -- politics, police, sports, community news. robots.txt (Yoast
default) disallows nothing for User-agent: * (only blocks AdsBot). WP
REST API confirmed live 2026-08-22: oldest indexed post 2010-04-21,
newest same-day as check, X-WP-Total 6604. per_page=100 + full
_embed/_fields timed ~6.2s -- no per_page override needed.
"""
from .wordpress import WordPressScraper


class LaBatallaScraper(WordPressScraper):
    name = "La Batalla de Maipú"
    base_url = "https://www.labatalla.cl"
    region = "metropolitana"
    min_delay = 1.0
