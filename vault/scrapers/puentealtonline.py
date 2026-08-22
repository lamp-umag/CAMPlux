"""
Puente Altonline — puentealtonline.cl
Covers Puente Alto, La Florida, San Bernardo. robots.txt: no crawl-delay/
disallow on wp-json. WP REST API confirmed live 2026-08-22: oldest
indexed post 2024-06-24 ("hello-world" welcome post, real content starts
immediately after), newest 2025-05-22, X-WP-Total 70 -- small,
dormant-but-real archive (no new posts in ~15 months as of this check;
sampled titles are genuine local community coverage, not placeholder
content). per_page=100 + full _embed/_fields timed ~4s. Given the tiny
size, did a one-time mode=full backfill instead of leaving it on the
narrow-range-only precedent -- see metropolitana.md.
"""
from .wordpress import WordPressScraper


class PuenteAltonlineScraper(WordPressScraper):
    name = "Puente Altonline"
    base_url = "https://puentealtonline.cl"
    region = "metropolitana"
    min_delay = 1.0
