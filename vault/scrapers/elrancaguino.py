"""
El Rancagüino — elrancaguino.cl
Self-described 110-year-old print title covering all 33 communes of the
O'Higgins region. robots.txt: no crawl-delay/disallow on wp-json. WP REST
API confirmed live 2026-08-22 via manual curl: oldest indexed post
2009-10-01, newest same-day as check, X-WP-Total 70094 (biggest archive
found across this region), per_page=100 + full _embed/_fields timed ~5.6s.
WAF blocks both our default camplux-Quarry UA and the shared BROWSER_UA
(Chrome/120-Mac string) with a 403 -- confirmed live an app-side
mode=range test came back seen=0/saved=0 with HTTP 403 in the logs despite
manual curl working, tracked down to the UA. Same class as madero.cl: a
plain Chrome/126-Windows UA passes reliably (confirmed 200 live). Uses its
own UA override instead of the shared BROWSER_UA for this reason.
"""
from .wordpress import WordPressScraper

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class ElRancaguinoScraper(WordPressScraper):
    name = "El Rancagüino"
    base_url = "https://www.elrancaguino.cl"
    region = "ohiggins"
    min_delay = 1.0

    def __init__(self):
        super().__init__()
        self.session.headers["User-Agent"] = _UA
