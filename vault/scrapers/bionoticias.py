"""
Bionoticias.cl — bionoticias.cl
Los Ángeles / Biobío province digital-native outlet, publishing since 2012.
robots.txt: no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2014-06-01, newest same-day as check,
X-WP-Total 31280 (largest archive found in this region). per_page=100 +
full _embed/_fields timed ~7.6s -- no override needed.
"""
from .wordpress import WordPressScraper


class BionoticiasScraper(WordPressScraper):
    name = "Bionoticias.cl"
    base_url = "https://bionoticias.cl"
    region = "biobio"
    min_delay = 1.0
