"""
Puente Alto Al Día — puentealtoaldia.com
Cordillera province (Puente Alto, Pirque, San José de Maipo), print since
1962. robots.txt: no crawl-delay/disallow on wp-json. WP REST API
confirmed live 2026-08-22: oldest indexed post 2024-04-10 (digital archive
much shallower than the print heritage), newest same-day as check,
X-WP-Total 1301. per_page=100 + full _embed/_fields timed ~4s -- no
per_page override needed.
"""
from .wordpress import WordPressScraper


class PuenteAltoAlDiaScraper(WordPressScraper):
    name = "Puente Alto Al Día"
    base_url = "https://puentealtoaldia.com"
    region = "metropolitana"
    min_delay = 1.0
