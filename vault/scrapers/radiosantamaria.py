"""
Radio Santa María — radiosantamaria.cl
Coyhaique, region's oldest/most prominent radio station (est. 1979).
robots.txt: general crawling allowed, no crawl-delay.
"""
from .wordpress import WordPressScraper


class RadioSantaMariaScraper(WordPressScraper):
    name = "Radio Santa María"
    base_url = "https://www.radiosantamaria.cl"
    region = "aysen"
    min_delay = 1.0
