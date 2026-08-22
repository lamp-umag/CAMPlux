# Arica y Parinacota — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Arica Hoy | https://www.aricahoy.cl | digital-native | yes (API live) | Self-described "diario electrónico." Confirmed JSON. |
| Arica365 | https://www.arica365.cl | digital-native | unknown/custom | Bare domain 302-redirects; following it, probe path returns HTML not JSON. Self-described "media center informativo" for the region. Needs closer look. |
| El Morrocotudo | https://www.elmorrocotudo.cl | digital-native | no | 301-redirects to a page where the probe returns 404. Site is built on the Bligoo publishing platform per search results (a proprietary CMS network used by several Chilean regional sites), not WordPress. |
| Arica al Día | https://www.aricaldia.cl | digital-native | yes (API live) | Confirmed JSON. Covers regional media-fund and local news. |
| La Estrella de Arica | https://www.estrellaarica.cl | newspaper | no | Not WordPress (404 on probe). Part of the "El Mercurio S.A.P." regional-newspaper chain (same group as El Diario de Atacama, La Estrella de Iquique) — long-running print daily with digital edition; likely a proprietary CMS, possibly metered/paywalled content given the chain's pattern elsewhere. Genuinely Arica-specific despite the corporate ownership, not a national outlet. |
| El Morro de Arica | https://elmorrodearica.cl | digital-native | yes (API live) | Confirmed JSON. |
| Cappissima Multimedial | https://cappissimamultimedial.cl | radio/TV | yes (API live) | FM 104.9 + local TV signal in Arica; confirmed JSON, so it runs a WP news site alongside broadcast. |

## Summary

Found 7 outlets for Arica y Parinacota — smaller haul than Aysén despite the larger population, likely because the region's press is concentrated in a handful of well-known names rather than many small hyperlocal sites. 4 of 7 (Arica Hoy, Arica al Día, El Morro de Arica, Cappissima Multimedial) are confirmed WordPress with a live open REST API. Telenorte Arica (regional TV) was investigated and ruled out immediately — it shut down in 2001 and has no current web presence, so it's omitted from the table entirely rather than padding it with a dead outlet.

## Phase 2 — implemented 2026-08-22

All 4 confirmed-WP candidates are live in production (`vault/scrapers/`,
registered under `app.py`'s `arica_parinacota` group). Verified with a real
`mode=range` test (2026-08-01 to 2026-08-22): Arica Hoy 68, Arica al Día
136, El Morro de Arica 57 real recent articles. `per_page=100`+`_embed`
timed 2.6-4.1s for all four — no override needed.

**Cappissima Multimedial needed a different move**: `seen=0` on the narrow
recent-range test, but NOT the ovejeronoticias-style silent failure — this
site genuinely has 1,527 real historical articles (2023-07-21 to
2025-11-21) but appears to have **stopped publishing to WordPress around
November 2025** (newest indexed post is 2025-11-21, ~9 months stale as of
today). Ran a one-time `mode=full` instead of relying on `mode=update`'s
date math — 1,527/1,527 saved cleanly, real content confirmed. Left
`nightly_enabled` at its default (true): unlike the `biobiochile`/
`cnnchile` 16-year-gap problem, this source's nightly `mode=update` window
just grows slowly (currently ~9 months and counting) rather than being
unboundedly pathological — cheap enough to leave alone, but worth
rechecking via `quality_check.py` or a manual look if it's still dormant
much longer.

Arica y Parinacota is DONE — both phases complete.
