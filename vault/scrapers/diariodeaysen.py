"""
Diario de Aysén — diariodeaysen.cl
Coyhaique-based. robots.txt: general crawling allowed, no crawl-delay.
"""
from .wordpress import WordPressScraper


class DiarioDeAysenScraper(WordPressScraper):
    name = "Diario de Aysén"
    base_url = "https://diariodeaysen.cl"
    region = "aysen"
    min_delay = 1.0
