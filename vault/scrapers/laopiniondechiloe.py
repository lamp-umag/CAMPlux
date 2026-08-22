"""
La Opinión de Chiloé — laopiniondechiloe.cl
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2015-02-08, X-WP-Total 5848, newest indexed
post 2026-07-19 (~1 month stale as of this check, not clearly dormant --
tested normally first). per_page=100 + full _embed/_fields timed ~7.2s --
no override needed.
"""
from .wordpress import WordPressScraper


class LaOpinionDeChiloeScraper(WordPressScraper):
    name = "La Opinión de Chiloé"
    base_url = "https://laopiniondechiloe.cl"
    region = "los_lagos"
    min_delay = 1.0
