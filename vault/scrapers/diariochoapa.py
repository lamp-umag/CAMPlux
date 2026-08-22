"""
Diario Choapa — diariochoapa.cl
Covers Illapel, Los Vilos, Salamanca, Canela (Choapa province). robots.txt:
no crawl-delay, no wp-json disallow. WP REST API confirmed live
2026-08-22: oldest indexed post 2021-07-17, X-WP-Total 1189 (real archive,
not a placeholder) -- but newest indexed post is 2026-03-05, ~5.5 months
stale as of this check. Dormant-but-real, same pattern as Cappissima
Multimedial / Los Ríos al Día -- got a one-time mode=full backfill instead
of relying on mode=update's narrow lookback. per_page=100 + full
_embed/_fields timed ~3.5s -- no override needed.
"""
from .wordpress import WordPressScraper


class DiarioChoapaScraper(WordPressScraper):
    name = "Diario Choapa"
    base_url = "https://diariochoapa.cl"
    region = "coquimbo"
    min_delay = 1.0
