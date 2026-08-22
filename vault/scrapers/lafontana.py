"""
La Fontana — lafontana.cl
Covers Chillán, San Carlos, Bulnes, Quirihue and more. robots.txt: Yoast
default block, "Disallow:" (empty) -- no crawl-delay, no wp-json disallow.
WP REST API confirmed live 2026-08-22: oldest indexed post 2020-04-16,
newest 2026-08-21, X-WP-Total 6505. per_page=100 + full _embed/_fields
timed ~3.2s -- no override needed.
"""
from .wordpress import WordPressScraper


class LaFontanaScraper(WordPressScraper):
    name = "La Fontana"
    base_url = "https://lafontana.cl"
    region = "nuble"
    min_delay = 1.0
