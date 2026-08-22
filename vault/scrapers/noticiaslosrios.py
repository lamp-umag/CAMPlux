"""
Noticias Los Ríos — noticiaslosrios.cl
robots.txt: no crawl-delay/disallow on wp-json. Note: one single post
(id 192343, a legal "extracto" notice) is indexed with date "0026-03-28"
instead of "2026-03-28" -- a data-entry typo on their end, not a scraper
bug; the site's real oldest post (via a same-request check on ?order=asc
after that anomaly) is from 2014-02-21, used as ARCHIVE_STARTS.
"""
from .wordpress import WordPressScraper


class NoticiasLosRiosScraper(WordPressScraper):
    name = "Noticias Los Ríos"
    base_url = "https://www.noticiaslosrios.cl"
    region = "los_rios"
    min_delay = 1.0
