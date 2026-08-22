"""
Radio Chilena del Maule — radiochilenadelmaule.cl
91.7/1090 Talca + 92.1 Molina, sister station Radio Familia. robots.txt: no
crawl-delay/disallow on wp-json. WP REST API confirmed live 2026-08-22:
oldest indexed post 2021-03-11, X-WP-Total only 31 -- dormant since the
newest indexed post, 2023-02-02 (confirmed real content, not a placeholder:
COVID-19 coverage, municipal news, real bylined titles, not theme-demo
filler). Dormant-but-real -- got a one-time mode=full backfill instead of
nightly rotation. per_page=100 + full _embed/_fields timed ~2.7s.
"""
from .wordpress import WordPressScraper


class RadioChilenaDelMauleScraper(WordPressScraper):
    name = "Radio Chilena del Maule"
    base_url = "https://radiochilenadelmaule.cl"
    region = "maule"
    min_delay = 1.0
