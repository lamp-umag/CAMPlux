"""
HDN Digital — hdn.cl
Covers Santa Cruz, Colchagua province, and the O'Higgins region. robots.txt
has "Crawl-delay: 10" -- min_delay set accordingly, same treatment as
Ovalle Hoy / Periódico Los Ríos precedents. WP REST API confirmed live
2026-08-22: oldest indexed post 2015-09-05, newest indexed post
2026-08-20, X-WP-Total 2244. per_page=100 + full _embed/_fields timed
~14.5s -- no per_page override needed.
"""
from .wordpress import WordPressScraper


class HdnScraper(WordPressScraper):
    name = "HDN Digital"
    base_url = "https://hdn.cl"
    region = "ohiggins"
    min_delay = 10.0
