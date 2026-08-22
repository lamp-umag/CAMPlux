"""
La Voz de Maipú — lavozdemaipu.cl
Maipú. Census flagged this as blocking the default curl User-Agent (403
with no UA at all), but re-verified live 2026-08-22 that our actual
project UA (camplux-Quarry/1.0, see base.py's HEADERS) already passes with
200 -- the site's WAF/Cloudflare rule only blocks bare/empty User-Agent
strings, not ours specifically. No use_browser_ua override needed.
robots.txt is the newer Cloudflare-managed Content-Signal format (blocks
named AI bots like GPTBot/ClaudeBot with Disallow: /, User-agent: * stays
Allow: /) -- doesn't affect our scraper's own UA, not disqualifying (same
pattern seen across recent regions). Site appears to be mid-migration to
an Astro frontend in front of the same WP backend (see robots.txt
comments about a "cutover") but /wp-json/ itself is untouched and fully
functional. WP REST API confirmed live 2026-08-22: oldest indexed post
2009-08-05 (deep historical archive), newest same-day as check, X-WP-Total
15888. per_page=100 + full _embed/_fields timed ~2.9s -- no per_page
override needed.
"""
from .wordpress import WordPressScraper


class LaVozDeMaipuScraper(WordPressScraper):
    name = "La Voz de Maipú"
    base_url = "https://lavozdemaipu.cl"
    region = "metropolitana"
    min_delay = 1.0
