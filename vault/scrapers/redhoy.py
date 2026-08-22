"""
RedHoy — redhoy.cl
Important finding from the phase-1 census, re-confirmed live 2026-08-22:
hoypuentealto.cl, hoy-vitacura.cl, hoypudahuel.cl, and hoysanbernardo.cl
are NOT four separate outlets. All four domains' /wp-json/ root report the
identical site identity ("name":"RedHoy","url":"https://redhoy.cl") and
serve byte-identical post content -- they're comuna-branded domain aliases
of one WordPress backend. redhoy.cl was picked as the canonical domain
(the one the backend itself self-identifies as). Only one scraper is
built for this network.

robots.txt: Cloudflare-managed Content-Signal format (blocks named AI bots
like GPTBot/ClaudeBot with Disallow: /, User-agent: * stays Allow: /) --
doesn't affect our scraper's own UA, not disqualifying. No Crawl-delay
for User-agent: *.

WP REST API confirmed live 2026-08-22: oldest indexed post 2025-01-01,
newest same-day as check, X-WP-Total 11722 (~19-20 posts/day -- a
comunal/regional aggregation network, consistent with its self-description
"La red Comunal y Regional de noticias que nos une").

use_embed=False required: redhoy.cl runs a custom REST plugin
(namespace "redhoy/v1") that rejects any _embed request from anonymous
callers with 403 {"code":"rh_rest_embed_blocked"} -- confirmed live,
reproduced with the default UA, the shared BROWSER_UA, and a plain
Chrome/126-Windows UA alike (all three still 403 with _embed present),
while the exact same request with _embed dropped returns 200 in under 1s.
This is a genuinely new failure mode for this project (not a UA/WAF
block like madero.cl/elrancaguino.cl -- those still needed a UA to pass
at all; this site works fine without a UA override, it specifically
blocks the _embed query param for anonymous requests). Cost: author name
and featured image are left blank for this source (see use_embed's
docstring in wordpress.py) -- the article title/date/link/body/categories
are all unaffected, those come from the plain /posts response.

**Second, more consequential custom restriction found live during range
testing (2026-08-22)**: the same plugin also caps anonymous pagination
depth at page 5, *regardless of per_page* -- confirmed live: page=5
returns 200, page=6 returns 403 {"code":"rh_rest_page_limited","message":
"Pagination depth limited for anonymous requests."} at per_page=100
*and* at per_page=20 alike. This means an anonymous caller (us) can only
ever reach the most recent 5*per_page posts -- with per_page=100, a
rolling window of ~500 posts, which at this site's ~19-20 posts/day pace
is roughly the last 25-26 days, not the full archive back to 2025-01-01.
**Do not attempt mode=full on this source** -- it cannot succeed, it will
just 403 through the remaining ~117 of ~122 pages. mode=update (nightly,
~2-day lookback) stays well inside the reachable window and works fine
indefinitely; this source is registered and range-tested only, same
register-and-defer judgment call as g5noticias in Valparaíso, but for a
different, harder reason (theirs was “too big to be worth it yet”; this
one is “anonymous access to the rest is deliberately blocked by the site
itself, no amount of waiting fixes it”). ARCHIVE_STARTS still records the
site's true oldest-indexed date for documentation purposes, not as a
promise that full history is reachable.
"""
from .wordpress import WordPressScraper


class RedHoyScraper(WordPressScraper):
    name = "RedHoy"
    base_url = "https://redhoy.cl"
    region = "metropolitana"
    min_delay = 1.0
    use_embed = False
