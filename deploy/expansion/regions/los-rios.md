# Los Ríos — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Diario de Valdivia | https://www.diariodevaldivia.cl | newspaper (digital) | yes (API live) | Valdivia city daily. |
| El Austral de Los Ríos | https://www.australvaldivia.cl | newspaper | possible WP, API blocked | Regional edition of the historic "El Austral" chain (El Mercurio group). Homepage has ~18 wp-content/wp-json references but `/wp-json/wp/v2/posts` returns 404 — REST route likely disabled. Needs closer look in phase 2. |
| Río en Línea | https://www.rioenlinea.cl | digital-native | yes (API live) | Independent, founded 2010; one of the region's oldest digital-native outlets. |
| Periódico Los Ríos | https://periodicolosrios.cl | newspaper (print + online) | yes (API live) | First outlet claiming 100% regional print+online distribution across all 12 communes. |
| El Naveghable | https://www.elnaveghable.cl | digital-native | no | Root loads (200) but zero wp-content/wp-json markers and wp-json 404 — likely a non-WP custom build. |
| Los Ríos al Día | https://www.losriosaldia.cl | digital-native | yes (API live) | |
| Noticias Los Ríos | https://www.noticiaslosrios.cl | digital-native | yes (API live) | |
| Diario Futrono | https://www.diariofutrono.cl | digital-native (comuna) | yes (API live) | Part of a comuna-by-comuna network spanning most of the region (Futrono, Panguipulli, La Unión, Río Bueno, Paillaco, Corral, Lago Ranco, Los Lagos, Máfil all have sister sites — see below). |
| Diario de Panguipulli | https://www.diariodepanguipulli.cl | digital-native (comuna) | yes (API live) | Same network as Diario Futrono. |
| Panguipulli Noticias | https://panguipullinoticias.cl | digital-native (comuna) | possible WP, API blocked | Separate outlet from Diario de Panguipulli. Root has ~400 wp-content/wp-json references (strong WP signal) but `/wp-json/` returns 404 — worth a closer look, might just need a different base path. |
| Diario Río Bueno | https://www.diarioriobueno.cl | digital-native (comuna) | yes (API live) | Same network as Diario Futrono. |
| NoticiasRioBueno.com | https://www.noticiasriobueno.com | digital-native (comuna) | yes (API live) | Separate outlet from Diario Río Bueno, also covering Río Bueno. |
| Diario La Unión | https://www.diariolaunion.cl | digital-native (comuna) | yes (API live) | Same network as Diario Futrono. |
| Diario Paillaco | https://www.diariopaillaco.cl | digital-native (comuna) | yes (API live) | Same network as Diario Futrono. |
| Diario El Ranco | https://diarioelranco.cl | digital-native (comuna) | yes (API live) | Covers La Unión / Río Bueno / Lago Ranco area, separate from the Diario Futrono network. |
| Diario Corral | https://www.diariocorral.cl | digital-native (comuna) | yes (API live) | Same network as Diario Futrono. |
| Diario Lago Ranco | https://www.diariolagoranco.cl | digital-native (comuna) | yes (API live) | Same network as Diario Futrono. |
| Diario Laguino | https://www.diariolaguino.cl | digital-native (comuna) | yes (API live) | Covers Los Lagos comuna; same network as Diario Futrono. |
| Diario Máfil | https://www.diariomafil.cl | digital-native (comuna) | yes (API live) | Same network as Diario Futrono. |
| Radio Austral Valdivia | https://www.radioaustralvaldivia.cl | radio (news site) | yes (API live) | 970 AM, Valdivia; generalist/informative station with a news-focused site. |

## Summary

19 outlets found, a strong showing for a mid-population region. The standout finding is a dense comuna-by-comuna WordPress network (Futrono, Panguipulli, La Unión, Río Bueno, Paillaco, Corral, Lago Ranco, Los Lagos, Máfil) that all returned a clean `200` on `/wp-json/wp/v2/posts` — essentially a batch of near-zero-effort integrations if phase 2 confirms `robots.txt` doesn't block them. 15 of 19 are WordPress with a live open API; 2 more (australvaldivia.cl, panguipullinoticias.cl) show strong WordPress fingerprints on the homepage but the REST route itself 404s, worth a second look in phase 2 rather than writing off. Only el naveghable and (implicitly) any print-only outlets look non-WordPress. No connectivity failures in this region, unlike Antofagasta/Coquimbo's chain outlets.

## Phase 2 — implemented 2026-08-22

**Important correction to the phase-1 census**: live re-verification found
that the entire "Diario Futrono network" (Futrono, Panguipulli, Río Bueno,
La Unión, Paillaco, Corral, Lago Ranco, Los Lagos/Laguino, Máfil — 9
domains) **plus Diario de Valdivia** (10 domains total) are **not actually
WordPress**, contrary to the census's "yes (API live)" verdict. Confirmed
live 2026-08-22: `/wp-json/wp/v2/posts` on every one of these 10 domains
returns `HTTP 200` with `Content-Type: text/html` (a plain HTML page, not
JSON) regardless of User-Agent (tested both default and a browser UA); none
of their homepages contain any `wp-content`/`wp-json`/`wp-includes`
fingerprints; and their `robots.txt` follows a completely different,
non-WordPress pattern shared across all 10 (`/templates/`,
`/base/printadv/`, `/estadset/`, `/base/clima.php`, `/admin/` — a
proprietary regional-chain CMS, not WP's usual `/wp-admin/`). This is
exactly the "confirmed live API isn't enough, always re-verify" lesson
from `diariodeaysen`, just for a false-positive-on-CMS-type instead of a
placeholder install. All 10 are documented in `DISABLED_SOURCES` in
`app.py` (region `los_rios`) with this finding; no scraper files were
created for them (matches the `elmagallanews` precedent — a non-viable
finding with no code, not an if-you-need-it retrofit).

**noticiasriobueno.com was also ruled out**: WP REST API genuinely works,
but `robots.txt` specifies `Crawl-delay: 3600` (one full hour) — 12x worse
than the `elmagallanews` precedent (300s) already ruled out for the same
reason. Documented in `DISABLED_SOURCES`, no scraper file.

**6 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `los_rios` group): **Radio Austral Valdivia, Los Ríos al Día,
Periódico Los Ríos, Noticias Los Ríos, Río en Línea, Diario El Ranco**.
None had a disqualifying robots.txt restriction (Periódico Los Ríos has
`Crawl-delay: 10` — set `min_delay = 10.0` on its scraper, well within
reason). `per_page=100` + full `_embed` timed 2.4-9.2s for all six — no
`per_page` override needed. Real body text confirmed for all six via a
spot-check.

Verified with a real `mode=range` test (2026-08-01 to 2026-08-22): Radio
Austral Valdivia 8, Noticias Los Ríos 251, Río en Línea 90, Diario El
Ranco 178 real recent articles saved cleanly.

**Los Ríos al Día and Periódico Los Ríos were dormant-but-real** (same
pattern as Cappissima Multimedial in Arica y Parinacota) — `seen=0` on the
narrow recent-range test, but both have genuine historical archives, just
stopped publishing recently (Los Ríos al Día newest indexed post
2026-06-12, ~2 months stale; Periódico Los Ríos newest 2026-05-05, ~3.5
months stale, as of today 2026-08-22). Ran a one-time `mode=full` for
both instead of relying on `mode=update`'s date math: Periódico Los Ríos
815/815 saved cleanly; Los Ríos al Día's backfill finished too (took ~16
min for its full 20,337-post archive, 2013-06-25 through 2026-06-12) —
20,337/20,337 total, all saved cleanly (17,837 new on the final run, the
rest already landed from an earlier partial pass before a container
rebuild interrupted it mid-flight — no duplicates, `INSERT OR IGNORE`
handled the overlap correctly). Left `nightly_enabled` at its default for
both (a growing-slowly dormancy gap, not an unbounded biobiochile-style
pathological one).

Noticias Los Ríos has one single data-entry-typo post (`0026-03-28`
instead of `2026-03-28`, a legal "extracto" notice) — used the site's real
oldest post (2014-02-21) for `ARCHIVE_STARTS` instead. Noted in the
scraper's docstring so nobody's confused by it later.

The 2 census "possible WP, API blocked" outlets (australvaldivia.cl,
panguipullinoticias.cl) were left untouched — out of this task's scope
(only "yes (API live)" outlets were re-verified/wired in this pass).

Los Ríos is DONE — both phases complete for the "yes (API live)" set from
the census; the 2 "possible WP, blocked" outlets remain open for a future
closer look.
