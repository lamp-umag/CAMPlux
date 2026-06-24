from .wordpress import WordPressScraper

class TheClinicScraper(WordPressScraper):
    name      = "The Clinic"
    base_url  = "https://www.theclinic.cl"
    region    = "nacional"
    min_delay = 1.0
