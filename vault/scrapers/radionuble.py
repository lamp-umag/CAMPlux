"""
Radio Ñuble — radionuble.cl
89.7 FM / 900 AM, Chillán. Site lives entirely under a /v1/ subpath (root
domain is something else) -- base_url includes it so the inherited _api
property builds the right wp-json path. robots.txt at the /v1/ subpath
404s (no robots.txt file present there) -- no disallow found, same
"404 = no disallow" precedent as iquiquealdia. WP REST API confirmed live
2026-08-22: oldest indexed post 2024-12-02, newest same-day as this check,
X-WP-Total 2944. per_page=100 + full _embed/_fields timed ~3.2s -- no
override needed.
"""
from .wordpress import WordPressScraper


class RadioNubleScraper(WordPressScraper):
    name = "Radio Ñuble"
    base_url = "https://radionuble.cl/v1"
    region = "nuble"
    min_delay = 1.0
