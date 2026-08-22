"""
Ñuble Online — nubleonline.cl
robots.txt: Yoast default block, "Disallow:" (empty) -- no crawl-delay, no
wp-json disallow. WP REST API confirmed live 2026-08-22: oldest indexed post
2023-04-18, newest same-day as this check, X-WP-Total 4877. per_page=100 +
full _embed/_fields timed ~2.3s -- no override needed.
"""
from .wordpress import WordPressScraper


class NubleOnlineScraper(WordPressScraper):
    name = "Ñuble Online"
    base_url = "https://nubleonline.cl"
    region = "nuble"
    min_delay = 1.0
