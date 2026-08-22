"""
Los Ríos al Día — losriosaldia.cl
robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class LosRiosAlDiaScraper(WordPressScraper):
    name = "Los Ríos al Día"
    base_url = "https://www.losriosaldia.cl"
    region = "los_rios"
    min_delay = 1.0
