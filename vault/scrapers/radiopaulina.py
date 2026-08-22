"""
Radio Paulina — radiopaulina.cl
Described as the most influential media outlet in Tarapacá; broadcasts
across the region (Iquique 89.3, Pica 101.7, Tocopilla 100.7) and into
Arica (94.5). robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class RadioPaulinaScraper(WordPressScraper):
    name = "Radio Paulina"
    base_url = "https://radiopaulina.cl"
    region = "tarapaca"
    min_delay = 1.0
