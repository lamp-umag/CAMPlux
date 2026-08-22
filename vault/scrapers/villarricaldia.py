"""
Villarrica al Día — census domain villarricaldia.cl, real live domain
vadmedia.cl
Covers Villarrica, Pucón, Lican Ray lake area. The census domain
(villarricaldia.cl) now 301-redirects to vadmedia.cl -- confirmed same
outlet via its own /wp-json/ "name" field ("Villarrica al dia") before
wiring in the new domain directly (avoids an extra redirect hop on every
request). robots.txt (vadmedia.cl): no crawl-delay/disallow on wp-json. WP
REST API confirmed live 2026-08-22: oldest indexed post 2023-05-10, newest
indexed post 2026-08-20 (~2 days stale as of this check, not dormant),
X-WP-Total 606. per_page=100 + full _embed/_fields timed ~6.4s -- no
override needed.
"""
from .wordpress import WordPressScraper


class VillarricaAlDiaScraper(WordPressScraper):
    name = "Villarrica al Día"
    base_url = "https://vadmedia.cl"
    region = "araucania"
    min_delay = 1.0
