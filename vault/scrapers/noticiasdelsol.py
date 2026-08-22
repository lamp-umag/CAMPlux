"""
Noticias del Sol — noticiasdelsol.cl
Talagante province: Peñaflor, Talagante, Padre Hurtado, El Monte, Isla de
Maipo. robots.txt: no crawl-delay/disallow on wp-json. WP REST API
confirmed live 2026-08-22: oldest indexed post 2023-02-08, newest
2026-08-02 (three weeks old as of this check -- still an active site,
just a lighter recent posting cadence), X-WP-Total 361. per_page=100 +
full _embed/_fields timed ~6.2s -- no per_page override needed.
"""
from .wordpress import WordPressScraper


class NoticiasDelSolScraper(WordPressScraper):
    name = "Noticias del Sol"
    base_url = "https://noticiasdelsol.cl"
    region = "metropolitana"
    min_delay = 1.0
