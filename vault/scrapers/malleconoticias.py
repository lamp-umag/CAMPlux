"""
Malleco Noticias — malleconoticias.cl
Covers Angol and the 11 communes of Malleco province. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2026-02-23, X-WP-Total 64 (small, real archive), but
newest indexed post is 2026-05-11, ~3.5 months stale as of this check.
Dormant-but-real, same pattern as Diario Choapa / Cappissima Multimedial --
got a one-time mode=full backfill instead of relying on mode=update's
narrow lookback. per_page=100 + full _embed/_fields timed ~4.5s -- no
override needed.
"""
from .wordpress import WordPressScraper


class MallecoNoticiasScraper(WordPressScraper):
    name = "Malleco Noticias"
    base_url = "https://www.malleconoticias.cl"
    region = "araucania"
    min_delay = 1.0
