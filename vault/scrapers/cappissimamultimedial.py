"""
Cappissima Multimedial — cappissimamultimedial.cl
FM 104.9 + local TV signal in Arica, runs a WP news site alongside broadcast.
robots.txt: clean.
"""
from .wordpress import WordPressScraper


class CappissimaMultimedialScraper(WordPressScraper):
    name = "Cappissima Multimedial"
    base_url = "https://cappissimamultimedial.cl"
    region = "arica_parinacota"
    min_delay = 1.0
