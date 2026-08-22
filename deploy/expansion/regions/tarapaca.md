# Tarapacá — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Diario El Longino | https://diariolongino.cl | newspaper (digital) | yes (API live) | Confirmed JSON. Covers Iquique, Alto Hospicio, and El Tamarugal — all 7 comunas of the region. |
| Iquique TV | https://iquiquetv.cl | TV | yes (API live) | Confirmed JSON. Digital TV channel with 2 TVD signals + VTR carriage; runs a WP-based news site alongside broadcast. |
| Iquique al Día | https://iquiquealdia.cl | digital-native | yes (API live) | Confirmed JSON. |
| El Boyaldía | https://www.elboyaldia.cl | digital-native | no | 301-redirects; probe at redirected location returns 404. Not WordPress at that path — needs closer look. |
| La Estrella de Iquique | https://www.estrellaiquique.cl | newspaper | no | Not WordPress (404 on probe). Part of the "El Mercurio S.A.P." regional chain (same group as El Diario de Atacama, La Estrella de Arica); founded 1966, long-running local daily, likely proprietary CMS. |
| Radio Paulina | https://radiopaulina.cl | radio | yes (API live) | Confirmed JSON. Described as the most influential media outlet in Tarapacá; broadcasts on multiple frequencies across the region (Iquique 89.3, Pica 101.7, Tocopilla 100.7) and reaches into Arica (94.5) too. |
| RTC Televisión (via CORMUDESI) | https://cormudesi.cl | TV (municipal) | yes (API live) | Confirmed JSON on the parent domain, but `cormudesi.cl` is the umbrella site for Iquique's municipal social-development corporation (education, health, etc.) — RTC is one department of it, not a dedicated news domain. Would need path/category filtering, not a clean whole-site scrape. Flag as needs a closer look before treating like a normal WP source. |

## Excluded as out of scope

`soyiquique.cl` (part of the national **SoyChile.cl** network, itself part of the El Mercurio digital group) was found in search results but excluded — it's a national-network regional page, not a standalone local outlet, same category as BioBioChile/La Tercera regional bureaus that this census is meant to skip.

## Summary

Found 7 outlets for Tarapacá. 5 of 7 (Diario El Longino, Iquique TV, Iquique al Día, Radio Paulina, and RTC/CORMUDESI with the caveat above) are confirmed WordPress with a live open REST API. The two "La Estrella"/"El Boyaldía" legacy-style outlets are not straightforward WordPress targets. Overall a solid, WordPress-heavy region for phase 2.

## Phase 2 — implemented 2026-08-22

All 5 confirmed-WP candidates are live in production (`vault/scrapers/`,
registered under `app.py`'s `tarapaca` group): **Diario El Longino, Iquique
TV, Iquique al Día, Radio Paulina, RTC Televisión (CORMUDESI)**. No
robots.txt Crawl-delay/Disallow on wp-json for any of them; none were
placeholder installs (all had real historical content, real recent
titles). Verified with a real `mode=range` test (2026-08-01 to 2026-08-22):
Diario El Longino 174, Iquique TV 38, Iquique al Día 44, Radio Paulina 344,
RTC/CORMUDESI 27 real articles saved, body text spot-checked and real for
all five.

**Iquique al Día needed a `per_page` override**: `per_page=100` with full
`_embed` timed out entirely (>35s), `per_page=50` also timed out,
`per_page=25` is a reliable ~1.5s — same slow-host-can't-resolve-_embed
class of issue as `ovejeronoticias.cl`. Set `per_page = 25` on
`IquiqueAlDiaScraper`.

**RTC/CORMUDESI (cormudesi.cl) census caveat resolved cleanly**: the
census flagged this as a municipal umbrella site needing path/category
filtering since RTC news is "one department." Live investigation found
the entire `/wp-json/wp/v2/posts` endpoint (all 54 posts as of 2026-08-22)
is already just RTC Noticias content (category id 24, `/rtc-noticias/`
path) — no other municipal content is mixed into the `post` post-type, so
it turned out to be a clean whole-site scrape after all, wired in as a
normal `WordPressScraper` subclass with no filtering logic needed. Small
and young archive (oldest indexed post 2026-07-13), worth rechecking later
as it accumulates more history.

Tarapacá is DONE — both phases complete.
