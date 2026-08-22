"""
Diario Cauquenes — diariocauquenes.cl
Same "Red de Diarios del Maule" chain as Diario Linares -- shares a common
network launch post ("la-voz-de-los-talquinos", 2020-12-03) with Diario
Talca and Diario Linares, but has its own large, distinct archive of real
Cauquenes-area content (confirmed live 2026-08-22, see diariotalca.py for
the shared-post finding). robots.txt: no crawl-delay/disallow on wp-json
(Yoast block). WP REST API confirmed live: oldest indexed post 2020-12-03,
newest same-day as check, X-WP-Total 6821. per_page=100 + full
_embed/_fields timed ~6.3s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioCauquenesScraper(WordPressScraper):
    name = "Diario Cauquenes"
    base_url = "https://diariocauquenes.cl"
    region = "maule"
    min_delay = 1.0
