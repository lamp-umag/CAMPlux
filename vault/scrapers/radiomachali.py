"""
Radio Machalí — radiomachali.cl
Founded 2018, covers Machalí/Rancagua/region. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2026-03-31 -- a genuinely thin archive (X-WP-Total 33),
site likely migrated to WordPress or started publishing there recently
rather than a placeholder install (real, distinct recent headlines, newest
indexed post 2026-08-15). per_page=100 + full _embed/_fields timed ~3.1s
-- no override needed.
"""
from .wordpress import WordPressScraper


class RadioMachaliScraper(WordPressScraper):
    name = "Radio Machalí"
    base_url = "https://radiomachali.cl"
    region = "ohiggins"
    min_delay = 1.0
