"""
Diario Aysén — diarioaysen.cl
Puerto Aysén-based (distinct outlet/domain from "Diario de Aysén").
robots.txt: general crawling allowed, no crawl-delay.
"""
from .wordpress import WordPressScraper


class DiarioAysenScraper(WordPressScraper):
    name = "Diario Aysén"
    base_url = "https://diarioaysen.cl"
    region = "aysen"
    min_delay = 1.0
