"""
Diario El Ranco — diarioelranco.cl
Covers La Unión / Río Bueno / Lago Ranco area. Separate outlet/domain from
the (non-WordPress) "Diario Futrono network" -- see los-rios.md phase 2
notes. robots.txt: no crawl-delay/disallow on wp-json.
"""
from .wordpress import WordPressScraper


class DiarioElRancoScraper(WordPressScraper):
    name = "Diario El Ranco"
    base_url = "https://diarioelranco.cl"
    region = "los_rios"
    min_delay = 1.0
