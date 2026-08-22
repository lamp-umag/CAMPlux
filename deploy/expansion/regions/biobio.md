# Biobío — media census

Researched: 2026-08-22

Scope note: outlets based in Chillán, San Carlos, and other Ñuble-province
cities were deliberately excluded even though several directories still
lump them in with "Región del Biobío" — Ñuble split off as its own region
in 2018 and has its own slot later in this expansion plan. This file only
covers the current Biobío region: Concepción, Arauco, and Biobío provinces
(Concepción, Talcahuano, Los Ángeles, Coronel, Lota, Arauco, Cañete, Tomé,
etc.).

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Diario Concepción | https://www.diarioconcepcion.cl | newspaper | no (404, custom) | Universidad de Concepción-owned digital paper, founded 2008. Prominent, well-established. |
| El Sur | https://www.elsur.cl | newspaper | no (404, custom) | Historic Concepción daily (founded 1882), largest circulation in region. Owned by Diario El Sur S.A. (same group as La Estrella de Concepción). |
| La Estrella de Concepción | https://www.estrellaconcepcion.cl | newspaper | no (404, custom) | Tabloid-style regional daily, owned by Diario El Sur S.A.; circulates across Concepción province. |
| Sabes.cl | https://sabes.cl | digital-native | no (200 but returns HTML, custom theme `theme-sabes`, not the WP API) | "El Diario digital del Gran Concepción" — active, modern-looking site. |
| Bionoticias.cl | https://bionoticias.cl | digital-native | **yes (API live)** | Los Ángeles / Biobío province, publishing since 2012. Good scraper candidate. |
| La Tribuna | https://www.latribuna.cl | newspaper | no (404, custom) | "El Diario de la provincia de Biobío", based in Los Ángeles. Also listed as the site for Radio San Cristóbal FM (no separate radio domain found). |
| El Contraste | https://elcontraste.cl | digital-native | **yes (API live)** | Los Ángeles / Biobío province digital news. Good scraper candidate. |
| Sur Actual | https://www.suractual.cl | digital-native | inconclusive (TLS/connection errors on repeated checks — site may be down, migrating, or blocking automated requests) | Covers Concepción province incl. Talcahuano. Worth a manual re-check later. |
| Diario Provincial | https://diarioprovincial.cl | digital-native | **yes (API live)** | Arauco province news. Good scraper candidate. |
| Araucovisión | https://araucovision.cl | digital-native / TV-adjacent portal | **yes (API live)** | Arauco province news portal. Good scraper candidate. |
| Lanalhue Noticias | https://www.lanalhuenoticias.cl | digital-native | no (404, custom or non-standard WP path) | Cañete / Arauco province digital outlet, also runs a YouTube channel. |
| Renacer de Arauco | (no longer online) | newspaper | n/a — defunct | Historical Arauco-province paper, appears to have ceased operations around 2009. Listed for completeness only; not viable. |
| Canal 9 (Bío-Bío Televisión) | https://www.canal9.cl | TV | no (404, custom) | Regional TV channel covering Biobío. |
| TVU (Televisión Universidad de Concepción) | https://www.tvu.cl | TV | no (404, custom) | University-owned regional TV/press outlet. |
| Radiomas | https://www.radiomas.cl | radio, digital-native | no (redirect then 404 on API path, custom) | Covers communes across Concepción/Arauco/Biobío provinces including Penco. |
| Radio El Carbón | https://www.elcarbon.cl | radio | inconclusive (HTTP 500 on repeated checks) | Lota-based radio station, on air since 1959. |
| Radio Llacolén | https://radiollacolen.com | radio (sports) | **yes (API live, though 0 posts matched the query — endpoint is real and functioning)** | Concepción sports-focused radio, 1600 AM. |
| Soy Concepción | https://www.soychile.cl/concepcion | digital-native | n/a — subsection of the national SoyChile network, not a standalone site | Included for completeness; not a distinct scrape target. |

## Summary

18 candidate outlets found (plus one confirmed-defunct paper kept for the
record). Four look WordPress-viable at a glance with a live, open REST API:
**Bionoticias.cl, El Contraste, Diario Provincial, Araucovisión**, plus
**Radio Llacolén** (API works but returned zero posts on the test query —
worth a second look before ruling in or out). The bigger, older-money
outlets (Diario Concepción, El Sur, La Estrella de Concepción, La Tribuna,
Canal 9, TVU) all run custom/proprietary CMSes with no exposed WP API —
consistent with them being established newspaper-group properties rather
than blog-style digital-native operations. Deliberately excluded
Chillán/Ñuble-region outlets and Radio Bío-Bío / BioBioChile (national,
already handled elsewhere per project scope).

## Phase 2 — implemented 2026-08-22

Re-verified all 5 census "yes (API live)" outlets live before wiring
anything in. Also cross-checked `elsur` against this region's finding
(El Sur, elsur.cl, 404/custom CMS) — already correctly disabled in
`DISABLED_SOURCES`, only needed its `region` field updated from the
generic `"regional"` to `"biobio"` to match the current per-region
convention (no behavior change, purely a bookkeeping fix).

**Radio Llacolén confirmed not viable** — `X-WP-Total: 0` on the native
`post` type, and `/wp-json/wp/v2/types` shows no custom post type with
news content either (just `post`, `page`, `attachment`, and internal
Elementor page-builder types). A real, live WordPress install with a
theme (homepage title "Radio Llacolén – La deportiva") but genuinely zero
published posts — same class as `diariodeaysen`'s empty install. Moved to
`DISABLED_SOURCES`, no scraper file.

**Sur Actual and Radio El Carbón, both census "inconclusive", were
re-checked and are still down** — `suractual.cl`/`www.suractual.cl` fail
to connect at all (no TLS handshake), `elcarbon.cl` returns HTTP 500. Left
undisturbed as documented-but-inconclusive in this file; not added to
`DISABLED_SOURCES` since they were never a "yes (API live)" false
positive, just still-broken sites worth another look in a future pass.

**4 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `biobio` group): **Bionoticias.cl, El Contraste, Diario
Provincial, Araucovisión**.

- **Bionoticias.cl** has this region's biggest archive (X-WP-Total 31280,
  oldest post 2014-06-01).
- **El Contraste**'s robots.txt carries the same Cloudflare-managed
  named-AI-bot exclusion list seen across several Maule sources (GPTBot,
  ClaudeBot, etc. `Disallow: /`, generic `User-agent: *` stays `Allow: /`)
  — doesn't block our scraper's own UA, same treatment as before.
- **Araucovisión** is a small but genuinely active archive (113 posts,
  oldest 2025-03-05) — not dormant, just a young/small outlet.
- No `per_page` or UA overrides needed anywhere in this region — every
  timing test (`per_page=100` + full `_embed`/`_fields`) came back under
  8s, well within the 30s budget.
