"""
Iquique al Día — iquiquealdia.cl
robots.txt: 404s (no robots.txt file present) -- no disallow found.
Their WP host can't resolve _embed (author+media) for a full 100-post page
within our 30s request timeout -- confirmed live: per_page=100 times out
entirely (>35s), per_page=50 also times out, per_page=25 is a reliable
~1.5s. Same class of issue as ovejeronoticias.cl -- see that scraper's
docstring.
"""
from .wordpress import WordPressScraper


class IquiqueAlDiaScraper(WordPressScraper):
    name = "Iquique al Día"
    base_url = "https://iquiquealdia.cl"
    region = "tarapaca"
    min_delay = 1.0
    per_page = 25
