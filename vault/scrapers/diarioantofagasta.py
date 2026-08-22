"""
El Diario de Antofagasta — www.diarioantofagasta.cl
The region's most-read digital outlet (~14 years old); covers Antofagasta,
Calama, San Pedro de Atacama, Tocopilla, Mejillones, Taltal. robots.txt:
Disallow on /cgi-bin/, /wp-admin/, /archives/, *?replytocom -- no
crawl-delay, no wp-json disallow. WP REST API confirmed live 2026-08-22:
oldest indexed post 2011-02-07 (region's deepest archive found so far),
newest same-day as this check, X-WP-Total 33174. per_page=100 + full
_embed/_fields timed ~3.3s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioAntofagastaScraper(WordPressScraper):
    name = "El Diario de Antofagasta"
    base_url = "https://www.diarioantofagasta.cl"
    region = "antofagasta"
    min_delay = 1.0
