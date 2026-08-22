"""
Radio Frutillar FM 96.7 — radiofrutillarfm.cl
Covers Frutillar/Llanquihue/Puerto Octay lake basin. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2023-07-20, X-WP-Total 229, newest indexed post
2026-08-08 (~2 weeks stale as of this check, not dormant). per_page=100 +
full _embed/_fields timed ~5.6s -- no override needed.
"""
from .wordpress import WordPressScraper


class RadioFrutillarFmScraper(WordPressScraper):
    name = "Radio Frutillar FM 96.7"
    base_url = "https://radiofrutillarfm.cl"
    region = "los_lagos"
    min_delay = 1.0
