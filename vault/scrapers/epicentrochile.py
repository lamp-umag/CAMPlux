"""
Epicentro Chile — epicentrochile.com
Based in Valparaíso/Viña; census flagged its framing as borderline between
regional and general-interest ("Chile y el mundo"), but it's a
Valparaíso-headquartered outlet, kept in this region like Coquimbo/
Ñuble's similar borderline calls elsewhere in this campaign. robots.txt:
no crawl-delay/disallow on wp-json. WP REST API confirmed live
2026-08-22: oldest indexed post 2012-07-18, newest same-day as check,
X-WP-Total 89779. per_page=100 + full _embed/_fields timed ~4.6s -- no
override needed.
"""
from .wordpress import WordPressScraper


class EpicentroChileScraper(WordPressScraper):
    name = "Epicentro Chile"
    base_url = "https://epicentrochile.com"
    region = "valparaiso"
    min_delay = 1.0
