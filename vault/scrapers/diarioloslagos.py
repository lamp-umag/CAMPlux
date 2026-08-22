"""
Diario Digital Los Lagos — diarioloslagos.cl
Covers Puerto Montt/Llanquihue and the region generally. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2025-10-06, newest same-day as check, X-WP-Total 1278.
per_page=100 + full _embed/_fields timed ~8.7s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioLosLagosScraper(WordPressScraper):
    name = "Diario Digital Los Lagos"
    base_url = "https://diarioloslagos.cl"
    region = "los_lagos"
    min_delay = 1.0
