"""
Diario El Longino — diariolongino.cl
Covers Iquique, Alto Hospicio, El Tamarugal -- all 7 comunas of Tarapacá.
robots.txt: only disallows /carrito/, /cart/, /checkout/ and cart query
params (WooCommerce boilerplate); no crawl-delay, no disallow on /wp-json.
"""
from .wordpress import WordPressScraper


class DiarioLonginoScraper(WordPressScraper):
    name = "Diario El Longino"
    base_url = "https://diariolongino.cl"
    region = "tarapaca"
    min_delay = 1.0
