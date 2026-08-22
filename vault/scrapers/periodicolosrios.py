"""
Periódico Los Ríos — periodicolosrios.cl
Claims 100% regional print+online distribution across all 12 communes.
robots.txt: Crawl-delay: 10 -- min_delay bumped to match. Disallows
/admin/, /includes/, /config/, /logs/, /backup/, /.env, /wp-includes/ --
none of which touch /wp-json/.
"""
from .wordpress import WordPressScraper


class PeriodicoLosRiosScraper(WordPressScraper):
    name = "Periódico Los Ríos"
    base_url = "https://periodicolosrios.cl"
    region = "los_rios"
    min_delay = 10.0
