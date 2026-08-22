"""
Radio Austral Valdivia — radioaustralvaldivia.cl
970 AM, Valdivia; generalist/informative station with a news-focused site.
robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class RadioAustralValdiviaScraper(WordPressScraper):
    name = "Radio Austral Valdivia"
    base_url = "https://www.radioaustralvaldivia.cl"
    region = "los_rios"
    min_delay = 1.0
