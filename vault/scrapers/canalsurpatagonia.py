"""
Canal Sur Patagonia — canalsurpatagonia.cl
Self-described independent digital outlet for the Aysén region.
robots.txt: general crawling allowed, no crawl-delay.
"""
from .wordpress import WordPressScraper


class CanalSurPatagoniaScraper(WordPressScraper):
    name = "Canal Sur Patagonia"
    base_url = "https://www.canalsurpatagonia.cl"
    region = "aysen"
    min_delay = 1.0
