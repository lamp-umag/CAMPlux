"""
Diario El Labrador — diarioellabrador.cl
Melipilla, founded 1921 (print). Note: the older diariolabrador.cl domain
is dead/unreachable, use diarioellabrador.cl. robots.txt: no crawl-delay/
disallow on wp-json (Yoast default). WP REST API confirmed live
2026-08-22: oldest indexed post 2025-03-07 (the site's digital archive
doesn't reach anywhere near the 1921 print history -- most likely digital
publishing only started recently), newest 2026-08-20, X-WP-Total 6805.
per_page=100 + full _embed/_fields timed ~4.8s -- no per_page override
needed. Oldest indexed post is a "digital edition" flipbook-embed post
(slug __trashed, mostly JS/iframe, thin body_text after HTML stripping) --
this is a minority post type mixed into an otherwise normal-article feed,
confirmed by sampling recent posts (real body text, 500-4000 chars).
"""
from .wordpress import WordPressScraper


class DiarioElLabradorScraper(WordPressScraper):
    name = "Diario El Labrador"
    base_url = "https://diarioellabrador.cl"
    region = "metropolitana"
    min_delay = 1.0
