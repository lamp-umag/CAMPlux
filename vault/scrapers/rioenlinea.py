"""
Río en Línea — rioenlinea.cl
Independent, founded 2010; one of the region's oldest digital-native
outlets. robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class RioEnLineaScraper(WordPressScraper):
    name = "Río en Línea"
    base_url = "https://www.rioenlinea.cl"
    region = "los_rios"
    min_delay = 1.0
