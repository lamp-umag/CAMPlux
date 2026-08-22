"""
El Morro de Arica — elmorrodearica.cl
robots.txt: clean, no crawl-delay/disallow found.
"""
from .wordpress import WordPressScraper


class ElMorroDeAricaScraper(WordPressScraper):
    name = "El Morro de Arica"
    base_url = "https://elmorrodearica.cl"
    region = "arica_parinacota"
    min_delay = 1.0
