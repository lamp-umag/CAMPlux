"""
CauquenesNet — cauquenesnet.cl
Covers Cauquenes, Chanco, Pelluhue. robots.txt: no crawl-delay/disallow on
wp-json. WP REST API confirmed live 2026-08-22: oldest indexed post
2000-03-12 -- checked for continuity (real digitized political-history
content, e.g. 2000/2001 posts about municipal elections and the "caravana
de la muerte" exhumations in Cauquenes, not a data-entry typo), same class
as diarioelmarino.cl's 1907 archive. Newest indexed post 2026-08-20,
X-WP-Total 20374. per_page=100 + full _embed/_fields timed ~3.7s -- no
override needed.
"""
from .wordpress import WordPressScraper


class CauquenesNetScraper(WordPressScraper):
    name = "CauquenesNet"
    base_url = "https://cauquenesnet.cl"
    region = "maule"
    min_delay = 1.0
