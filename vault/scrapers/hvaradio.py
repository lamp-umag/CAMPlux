"""
HVA Radio — hvaradio.cl
Self-described "La Radio de la Región de Atacama" (Vallenar). robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class HvaRadioScraper(WordPressScraper):
    name = "HVA Radio"
    base_url = "https://www.hvaradio.cl"
    region = "atacama"
    min_delay = 1.0
