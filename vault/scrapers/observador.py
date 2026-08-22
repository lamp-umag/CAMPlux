"""
El Observador — observador.cl
Covers Quillota, Petorca, San Felipe, Marga Marga and Valparaíso
provinces. robots.txt: no crawl-delay/disallow on wp-json (only assorted
Disallow rules for admin/comments/tags/attachments -- none touch
/wp-json/). WP REST API confirmed live 2026-08-22: oldest indexed post
2016-10-20, newest same-day as check, X-WP-Total 38526. per_page=100 +
full _embed/_fields timed ~7.2s -- no override needed.
"""
from .wordpress import WordPressScraper


class ObservadorScraper(WordPressScraper):
    name = "El Observador"
    base_url = "https://observador.cl"
    region = "valparaiso"
    min_delay = 1.0
