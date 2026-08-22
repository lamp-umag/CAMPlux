"""
Diario Rancagua — diariorancagua.cl
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2013-10-31, newest same-day as check,
X-WP-Total 18343. Their WP host can't resolve _embed (author+media) for a
full 100-post page within our 30s request timeout -- confirmed live:
per_page=100 times out (~35s, over budget), per_page=50 is too close to
the timeout to trust (~20.6s), per_page=25 is a reliable ~9.8s (checked
twice). Same class of issue as ovejeronoticias.cl / iquiquealdia.cl.
"""
from .wordpress import WordPressScraper


class DiarioRancaguaScraper(WordPressScraper):
    name = "Diario Rancagua"
    base_url = "https://diariorancagua.cl"
    region = "ohiggins"
    min_delay = 1.0
    per_page = 25
