"""
Diario Linares — diariolinares.cl
Part of the self-described "Red de Diarios del Maule" chain along with
Diario Cauquenes -- shares a common network launch post
("la-voz-de-los-talquinos", 2020-12-03) with Diario Talca and Diario
Cauquenes, but has its own large, distinct archive of real Linares-area
content (confirmed live 2026-08-22, see diariotalca.py for the shared-post
finding). robots.txt: no crawl-delay/disallow on wp-json (Yoast block).
WP REST API confirmed live: oldest indexed post 2020-12-03, newest
same-day as check, X-WP-Total 7687. per_page=100 + full _embed/_fields
timed ~5.9s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioLinaresScraper(WordPressScraper):
    name = "Diario Linares"
    base_url = "https://diariolinares.cl"
    region = "maule"
    min_delay = 1.0
