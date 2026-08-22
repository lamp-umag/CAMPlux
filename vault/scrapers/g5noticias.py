"""
G5 Noticias — g5noticias.cl
Multiplatform news from Valparaíso region professionals. robots.txt: no
crawl-delay/disallow on wp-json (only Disallow: /ads). WP REST API
confirmed live 2026-08-22: oldest indexed post 2020-01-08, newest same-day
as check, X-WP-Total 218838 -- this region's biggest archive by far,
confirmed genuine (real local news content: fires, ministers,
municipalities), not a duplicate/multisite artifact. per_page=100 + full
_embed/_fields timed ~6.4s -- no override needed. Given the archive size,
a full historical backfill will take a long time (see nightly_archive.py's
own docstring on why that's a deliberate, separate step) -- not run as
part of this initial wiring-in.
"""
from .wordpress import WordPressScraper


class G5NoticiasScraper(WordPressScraper):
    name = "G5 Noticias"
    base_url = "https://g5noticias.cl"
    region = "valparaiso"
    min_delay = 1.0
