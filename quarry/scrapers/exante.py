from .wordpress import WordPressScraper

class ExAnteScraper(WordPressScraper):
    name           = "Ex-Ante"
    base_url       = "https://ex-ante.cl"
    region         = "nacional"
    min_delay      = 1.0
    use_browser_ua = True
    enabled        = False
    note           = "WAF bloquea acceso (HTTP 403). Pendiente otra estrategia."
