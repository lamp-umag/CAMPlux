"""
Radio Nuevo Mundo — radionuevomundo.cl
104.7 FM Antofagasta; multi-city chain station with a national/regional
news mix. robots.txt: Yoast default block, "Disallow:" (empty) -- no
crawl-delay, no wp-json disallow. WP REST API confirmed live 2026-08-22:
oldest indexed post 2017-01-03, newest same-day as this check, X-WP-Total
14326. per_page=100 + full _embed/_fields timed ~4.5s -- no override
needed.
"""
from .wordpress import WordPressScraper


class RadioNuevoMundoScraper(WordPressScraper):
    name = "Radio Nuevo Mundo"
    base_url = "https://radionuevomundo.cl"
    region = "antofagasta"
    min_delay = 1.0
