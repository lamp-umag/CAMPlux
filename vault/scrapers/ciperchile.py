from .wordpress import WordPressScraper

class CiperChileScraper(WordPressScraper):
    name      = "CIPER Chile"
    base_url  = "https://ciperchile.cl"
    region    = "nacional"
    min_delay = 1.5
