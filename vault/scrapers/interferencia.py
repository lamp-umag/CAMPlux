from .wordpress import WordPressScraper

class InterferenciaScraper(WordPressScraper):
    name           = "Interferencia"
    base_url       = "https://interferencia.cl"
    region         = "nacional"
    min_delay      = 1.5
    use_browser_ua = True
