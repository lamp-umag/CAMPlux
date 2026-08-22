"""
RTC Televisión (via CORMUDESI) — cormudesi.cl
Census flagged this as needing a closer look: cormudesi.cl is the umbrella
site for Iquique's municipal social-development corporation, with RTC news
as one department, not a dedicated news domain. Investigated live
2026-08-22: turns out ALL of the site's "post" content type (X-WP-Total on
/wp-json/wp/v2/posts) is RTC Noticias (category id 24, URL path
/rtc-noticias/) -- there's no other content mixed into the posts endpoint
to filter out, so this is a clean whole-site scrape after all, no category
filtering needed. Small archive (54 posts total as of 2026-08-22, oldest
indexed 2026-07-13) -- a young or newly-WordPress-ified news operation.
robots.txt: "Allow: /", no crawl-delay/disallow.
"""
from .wordpress import WordPressScraper


class RtcCormudesiScraper(WordPressScraper):
    name = "RTC Televisión (CORMUDESI)"
    base_url = "https://cormudesi.cl"
    region = "tarapaca"
    min_delay = 1.0
