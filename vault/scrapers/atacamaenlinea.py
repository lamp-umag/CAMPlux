"""
Atacama en Línea — atacamaenlinea.cl
Self-described "Diario Independiente, Pluralista y Regional." robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class AtacamaEnLineaScraper(WordPressScraper):
    name = "Atacama en Línea"
    base_url = "https://www.atacamaenlinea.cl"
    region = "atacama"
    min_delay = 1.0
