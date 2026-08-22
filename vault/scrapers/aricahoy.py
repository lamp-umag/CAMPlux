"""
Arica Hoy — aricahoy.cl
Self-described "diario electrónico." robots.txt: no crawl-delay/disallow found.
"""
from .wordpress import WordPressScraper


class AricaHoyScraper(WordPressScraper):
    name = "Arica Hoy"
    base_url = "https://www.aricahoy.cl"
    region = "arica_parinacota"
    min_delay = 1.0
