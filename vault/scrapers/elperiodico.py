"""
El Periódico — elperiodico.cl
Covers Temuco and the region. robots.txt: no crawl-delay/disallow on
wp-json. WP REST API confirmed live 2026-08-22: oldest indexed post
2025-07-09 (a genuinely thin/newer archive, X-WP-Total 1100 -- real,
distinct recent headlines, not a placeholder), newest same-day as check.
per_page=100 + full _embed/_fields timed ~3.5s -- no override needed.
"""
from .wordpress import WordPressScraper


class ElPeriodicoScraper(WordPressScraper):
    name = "El Periódico"
    base_url = "https://elperiodico.cl"
    region = "araucania"
    min_delay = 1.0
