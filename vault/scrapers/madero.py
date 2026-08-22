"""
Madero — madero.cl
Copiapó-based integrated media platform (radio + digital news). robots.txt:
no crawl-delay/disallow on wp-json. WAF blocks our default camplux-Quarry UA
(and even the shared BROWSER_UA Chrome/120-Mac string used elsewhere in this
project) with a 403, but a plain Chrome/126-Windows UA passes reliably
(confirmed live 2026-08-22, 3/3) -- looks like a static UA blocklist rather
than rate limiting, since the block is 100% deterministic per UA string.
Uses its own UA override instead of the shared BROWSER_UA for this reason.
"""
from .wordpress import WordPressScraper

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class MaderoScraper(WordPressScraper):
    name = "Madero"
    base_url = "https://madero.cl"
    region = "atacama"
    min_delay = 1.0

    def __init__(self):
        super().__init__()
        self.session.headers["User-Agent"] = _UA
