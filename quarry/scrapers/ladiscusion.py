from .wordpress import WordPressScraper

class LaDiscusionScraper(WordPressScraper):
    name      = "La Discusión"
    base_url  = "https://www.ladiscusion.cl"
    region    = "regional"
    min_delay = 1.5
