"""
Ovalle Hoy — ovallehoy.cl
Ovalle-focused digital daily. robots.txt: Crawl-Delay: 20 (respected via
min_delay -- well within reason, same class as Periódico Los Ríos's
Crawl-Delay: 10 precedent). No wp-json disallow. WP REST API confirmed live
2026-08-22: oldest indexed post 2014-07-19, newest 2026-08-21, X-WP-Total
29939. per_page=100 + full _embed/_fields timed ~5.6s -- no per_page
override needed, still comfortably inside the 30s request timeout.
"""
from .wordpress import WordPressScraper


class OvalleHoyScraper(WordPressScraper):
    name = "Ovalle Hoy"
    base_url = "https://ovallehoy.cl"
    region = "coquimbo"
    min_delay = 20.0
