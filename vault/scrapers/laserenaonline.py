"""
La Serena Online — laserenaonline.cl
Covers La Serena, Coquimbo, Ovalle, Illapel, Vicuña and more. robots.txt:
no crawl-delay, no wp-json disallow. WP REST API confirmed live 2026-08-22:
newest indexed post today (2026-08-22), X-WP-Total 47939 (largest archive
found in Coquimbo). One single post has a data-entry-typo year
("0027-10-22" instead of a real date, id 115798, "Familias de sector Parte
Alta de Coquimbo...") -- same class of typo as noticiaslosrios's
"0026-03-28" finding. Used the site's real oldest post (2015-08-10) for
ARCHIVE_STARTS instead. per_page=100 + full _embed/_fields timed ~5.3s --
no override needed.
"""
from .wordpress import WordPressScraper


class LaSerenaOnlineScraper(WordPressScraper):
    name = "La Serena Online"
    base_url = "https://laserenaonline.cl"
    region = "coquimbo"
    min_delay = 1.0
