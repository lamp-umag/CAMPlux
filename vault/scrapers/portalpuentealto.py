"""
Portal Puente Alto — www.portalpuentealto.cl
Covers Puente Alto, La Florida, Pirque, Cajón del Maipo. robots.txt only
sets a Crawl-delay for Twitterbot specifically (not User-agent: *), so no
min_delay override is warranted. WP REST API confirmed live 2026-08-22:
oldest indexed post 2002-09-04 (deep, genuine historical archive, one of
the biggest found in this region), newest same-day as check, X-WP-Total
18303. per_page=100 + full _embed/_fields timed ~3.6s -- no per_page
override needed.
"""
from .wordpress import WordPressScraper


class PortalPuenteAltoScraper(WordPressScraper):
    name = "Portal Puente Alto"
    base_url = "https://www.portalpuentealto.cl"
    region = "metropolitana"
    min_delay = 1.0
