"""
Diario Regionalista Antofagasta — regionalista.cl
Independent, investigative-leaning; covers Antofagasta, Calama, Tocopilla,
Taltal, San Pedro de Atacama, Ollagüe, Sierra Gorda, Mejillones, María
Elena. robots.txt: standard Disallow: /wp-admin/ only -- no crawl-delay, no
wp-json disallow. WP REST API confirmed live 2026-08-22: oldest indexed
post 2018-03-05, newest 2026-08-21, X-WP-Total 9350. per_page=100 + full
_embed/_fields timed ~2.5s -- no override needed.
"""
from .wordpress import WordPressScraper


class RegionalistaScraper(WordPressScraper):
    name = "Diario Regionalista Antofagasta"
    base_url = "https://regionalista.cl"
    region = "antofagasta"
    min_delay = 1.0
