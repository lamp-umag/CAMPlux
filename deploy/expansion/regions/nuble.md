# Ñuble — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| La Discusión | https://ladiscusion.cl | newspaper (digital) | yes (API live) | "El Diario de la Región de Ñuble" — the region's oldest/biggest regional daily, Chillán-based. |
| Ñuble Online | https://nubleonline.cl | digital-native | yes (API live) | Independent, region-wide focus. |
| Ñuble Actual | https://www.nubleactual.cl | digital-native | yes (API live) | |
| La Fontana | https://lafontana.cl | digital-native | yes (API live) | Covers Chillán, San Carlos, Bulnes, Quirihue and more. |
| Quirihue Noticias | https://quirihuenoticias.cl | digital-native (comuna) | yes (API live) | Quirihue / Ñuble province. |
| Órbita Noticias | https://orbitanoticias.cl | digital-native | yes (API live) | Covers Ñuble and Quirihue. |
| ChillánOnline | https://www.chillanonline.cl | digital-native | possible WP, API blocked | Root has ~109 wp-content/wp-json references (strong WP signal) but `/wp-json/` returns 404 — worth a closer look in phase 2. |
| San Carlos Online | https://www.sancarlosonline.cl | digital-native (comuna) | no / unknown | Root loads (200), zero WP markers, wp-json 404 — likely non-WP or a different CMS. |
| Radio Ñuble | https://radionuble.cl/v1 | radio (news site) | yes (API live) | 89.7 FM / 900 AM, Chillán. Site lives under a `/v1/` subpath; API confirmed live there. |
| Radio Contacto 90.7 FM | https://radiocontacto.cl | radio (news site) | yes (API live) | Chillán/Ñuble news + music station. |
| Canal 21 Chillán | https://www.canal21tv.cl | TV | unknown / connection error | Both plain curl and a browser-UA retry timed out completely (no response, not even a TLS handshake) — inconclusive, needs a closer look (site may be down, geo-blocked, or behind aggressive bot protection). |

## Not included

- SoyChillán (soychile.cl/chillan) — deliberately excluded: it's a subpage of the national SoyChile platform (El Mercurio group), not a standalone regional outlet, same category as the already-out-of-scope national outlets.
- "Diario La Provincia" (mentioned in a government funding announcement as one of 21 funded Ñuble outlets) — no working website could be found under that name; searches only surfaced an unrelated Argentine paper of the same name. Not listed for lack of a verifiable URL.
- El Diario de Ñuble — only a Facebook page was found, no standalone website located.

## Summary

11 outlets found with real online presence, on the lower end of the expected 5-20 range but still solid for a region of ~512k people. 8 of 11 are confirmed WordPress with a live open API (including Radio Ñuble, once you find its `/v1/` subpath). ChillánOnline shows WordPress fingerprints but its API route is blocked/404, worth a second pass. Canal 21 (the region's local TV) is a genuine connectivity dead-end right now, not just a "not WordPress" case — flagged for a closer look. San Carlos Online looks non-WordPress.

## Phase 2 — implemented 2026-08-22

Re-verified all 8 census "yes (API live)" outlets live before wiring anything
in. One important note: **La Discusión was already a registered source**
(`ladiscusion`, under `app.py`'s `regional` group / `SOURCE_GROUPS["regional"]`)
from before this campaign started — it's Ñuble's own outlet but was
integrated separately, pre-dating the region-by-region rollout. Left it
untouched per this task's scope (don't touch existing sources); it's not
duplicated under the new `nuble` group.

**Órbita Noticias (orbitanoticias.cl) was ruled out** — this is a genuine
census false positive, different flavor from the Los Ríos "wrong CMS" case:
confirmed live 2026-08-22 that *every* request to the domain (homepage root
included, not just `/wp-json/`) returns `HTTP 200` with `content-length: 0`
— a completely empty body, regardless of User-Agent. The whole server is
serving nothing, not just blocking the REST route. Documented in
`DISABLED_SOURCES` (`app.py`, region `nuble`), no scraper file.

**6 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `nuble` group): **Ñuble Online, Ñuble Actual, La Fontana,
Quirihue Noticias, Radio Contacto 90.7 FM, Radio Ñuble**. None had a
disqualifying `robots.txt` restriction (no Crawl-delay, no wp-json
disallow on any of the six; `radionuble.cl/v1/robots.txt` 404s outright,
same "404 = no disallow" read as `iquiquealdia`). `per_page=100` + full
`_embed`/`_fields` timed 2.1-3.6s for all six — no `per_page` override
needed, no UA blocking encountered (default UA worked everywhere). Radio
Ñuble needed only a `base_url` that includes its `/v1/` subpath — no other
override, the inherited `_api` property builds the right path from that
automatically.

Verified with a real `mode=range` test (2026-08-01 to 2026-08-22, all
`seen == saved`, no duplicates skipped): Ñuble Online 160, Ñuble Actual 447,
La Fontana 73, Quirihue Noticias 44, Radio Contacto 449, Radio Ñuble 75 —
all real recent articles saved cleanly. Real body text (1-4.5KB per
article) and, for three of the six (Ñuble Actual, Quirihue Noticias, Radio
Ñuble), a real author byline confirmed via spot-check.

`ARCHIVE_STARTS` set to each site's real oldest-indexed post (confirmed via
`?orderby=date&order=asc`, not guessed): Ñuble Online 2023-04-18, Ñuble
Actual 2023-10-30, La Fontana 2020-04-16, Quirihue Noticias 2021-06-19,
Radio Contacto 2021-12-07, Radio Ñuble 2024-12-02. Left `nightly_enabled`
at its default for all six — no dormancy, all had a fresh post within the
last 2 days.

The 2 census "possible WP, blocked"/"unknown" outlets (ChillánOnline,
Canal 21) and the 1 non-WP outlet (San Carlos Online) were left untouched —
out of this task's scope (only "yes (API live)" outlets were
re-verified/wired in this pass).

Ñuble is DONE — both phases complete for the "yes (API live)" set from the
census.
