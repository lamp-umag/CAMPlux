"""
ChiloeNews — chiloenews.cl
Independent Chiloé-focused digital outlet, Cloudflare-fronted. robots.txt:
no crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2021-06-01, newest same-day as check, X-WP-Total 2833.
per_page=100 + full _embed/_fields timed ~15.1s (slower than most, likely
Cloudflare overhead, but comfortably within the 30s request timeout) -- no
override needed.
"""
from .wordpress import WordPressScraper


class ChiloeNewsScraper(WordPressScraper):
    name = "ChiloeNews"
    base_url = "https://chiloenews.cl"
    region = "los_lagos"
    min_delay = 1.0
