"""
El Contraste — elcontraste.cl
Los Ángeles / Biobío province digital news. robots.txt: only blocks named
AI-crawler bots (GPTBot, ClaudeBot, etc. via a Cloudflare-managed block)
with Disallow: / -- generic User-agent is Allow: /, no Crawl-delay or
Disallow on wp-json for us (same pattern as several Maule sources, see
diariotalca.py). WP REST API confirmed live 2026-08-22: oldest indexed
post 2019-03-10, newest same-day as check, X-WP-Total 28971. per_page=100
+ full _embed/_fields timed ~3.6s -- no override needed.
"""
from .wordpress import WordPressScraper


class ElContrasteScraper(WordPressScraper):
    name = "El Contraste"
    base_url = "https://elcontraste.cl"
    region = "biobio"
    min_delay = 1.0
