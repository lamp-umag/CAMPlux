"""
Atacama Noticias — atacamanoticias.cl
Self-described "Diario Oficial de Atacama." robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class AtacamaNoticiasScraper(WordPressScraper):
    name = "Atacama Noticias"
    base_url = "https://www.atacamanoticias.cl"
    region = "atacama"
    min_delay = 1.0
