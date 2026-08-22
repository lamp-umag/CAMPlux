"""
Portal de Melipilla — www.portaldemelipilla.cl
Melipilla province digital newspaper. robots.txt: no crawl-delay/disallow
on wp-json. WP REST API confirmed live 2026-08-22: oldest indexed post
2017-01-09, newest 2026-08-21, X-WP-Total 6670. per_page=100 + full
_embed/_fields timed a consistent ~16s (checked twice) -- slower than most
of this region's other sources but comfortably within the 30s request
timeout, same judgment call as elaconcagua.cl (~14.2s) / hdn.cl (~14.5s);
no per_page override applied.
"""
from .wordpress import WordPressScraper


class PortalDeMelipillaScraper(WordPressScraper):
    name = "Portal de Melipilla"
    base_url = "https://www.portaldemelipilla.cl"
    region = "metropolitana"
    min_delay = 1.0
