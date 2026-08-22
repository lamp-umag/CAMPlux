"""
Ovejero Noticias — ovejeronoticias.cl
robots.txt: blocks ClaudeBot and other AI crawlers by name; general crawling allowed.
Our quarry UA is not blocked. No crawl-delay.
"""
from .wordpress import WordPressScraper


class OvejeroNoticiasScraper(WordPressScraper):
    name = "Ovejero Noticias"
    base_url = "https://www.ovejeronoticias.cl"
    min_delay = 1.0
    # Their WP host can't resolve _embed (author+media) for a full 100-post
    # page within our 30s request timeout -- confirmed live: per_page=100
    # times out entirely (>60s), per_page=25 takes ~23s (too close to the
    # timeout to trust), per_page=10 is a reliable ~11s. This is why every
    # nightly `mode=update` since at least 2026-05 silently produced
    # seen=0/saved=0 (page 1 failed after 3 retries, no exception raised,
    # job_status still came back "done" -- see 2026-08-22 investigation).
    per_page = 10
