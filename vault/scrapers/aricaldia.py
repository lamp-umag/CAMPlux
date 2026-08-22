"""
Arica al Día — aricaldia.cl
Covers regional media-fund grants and local news. robots.txt: clean.
"""
from .wordpress import WordPressScraper


class AricaAlDiaScraper(WordPressScraper):
    name = "Arica al Día"
    base_url = "https://www.aricaldia.cl"
    region = "arica_parinacota"
    min_delay = 1.0
