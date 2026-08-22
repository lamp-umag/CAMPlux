"""
Diario Talca — diariotalca.cl
Flagship of an in-region multi-city network sharing a common launch post
("la-voz-de-los-talquinos", 2020-12-03) with Diario Linares and Diario
Cauquenes -- confirmed live 2026-08-22 that each domain otherwise has its
own distinct, large archive of real local content (different X-WP-Total,
different recent posts specific to each city), so this is a shared network
seed post, not a mirrored/duplicate install. robots.txt: only blocks named
AI-crawler bots (GPTBot, ClaudeBot, etc. via a Cloudflare-managed block) --
no Crawl-delay or Disallow on wp-json for a generic User-agent. WP REST API
confirmed live: oldest indexed post 2020-12-03, newest same-day as check,
X-WP-Total 20421. per_page=100 + full _embed/_fields timed ~7.3s -- no
override needed.
"""
from .wordpress import WordPressScraper


class DiarioTalcaScraper(WordPressScraper):
    name = "Diario Talca"
    base_url = "https://diariotalca.cl"
    region = "maule"
    min_delay = 1.0
