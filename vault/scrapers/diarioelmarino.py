"""
El Marino — diarioelmarino.cl
Covers Cardenal Caro province (Pichilemu area), self-described founding
2013, but its WordPress archive includes a real digitized historical
collection dated back to 1907 (five sequential posts timestamped
1907-08-18 -- a batch-imported historic-newspaper digitization, not a
data-entry typo like the laserenaonline/noticiaslosrios single-post
anomalies). robots.txt only disallows MJ12bot and Googlebot-Image, no
general Crawl-delay or wp-json block for our UA. WP REST API confirmed
live 2026-08-22: oldest indexed post 1907-08-18, newest same-day as check,
X-WP-Total 18345. per_page=100 + full _embed/_fields timed ~3.9s -- no
override needed.
"""
from .wordpress import WordPressScraper


class DiarioElMarinoScraper(WordPressScraper):
    name = "El Marino"
    base_url = "https://www.diarioelmarino.cl"
    region = "ohiggins"
    min_delay = 1.0
