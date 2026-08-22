# Araucanía — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Araucanía Noticias | https://araucanianoticias.cl | digital-native | yes (API live) | Confirmed live JSON. Independent, Temuco-based, founded 2011. |
| El Periódico | https://elperiodico.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. Covers Temuco and the region. |
| Malleco Noticias | https://www.malleconoticias.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. Covers Angol and the 11 communes of Malleco province. |
| Angol Noticias | https://www.angolnoticiasnew.cl | digital-native | yes (API live) | Confirmed live JSON. Self-described main digital news outlet of Malleco province. |
| Las Noticias de Malleco | https://lasnoticiasdemalleco.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. Claims to be the oldest continuously-published written outlet in the Araucanía region. |
| El Espejo de Malleco | https://elespejodemalleco.cl | newspaper (digital) | yes (API live) | Confirmed live JSON, active recent posts. Angol-based, covers Malleco province. |
| Malleco 7 | https://www.malleco7.cl | digital-native | yes (API live) | Confirmed live JSON, active recent posts. |
| Red Informativa (Villarrica) | https://radio.redinformativa.cl | radio/digital-native | yes (API live) | Bare domain redirects; confirmed live JSON on the resolved host. Covers Villarrica, Pucón, Lican Ray; runs FM stations in both towns. |
| Noticias del Lago | https://www.noticiasdellago.cl | digital-native | yes (API live) | Bare domain redirects to `www.`; confirmed live JSON. Covers Villarrica/Pucón lake area. |
| Pucón Radio | https://www.puconradio.cl | radio | yes (API live) | Bare domain redirects; confirmed live JSON. Has a dedicated news tag/section. |
| Villarrica al Día | https://www.villarricaldia.cl | digital-native | yes (API live) | Bare domain redirects to `www.`; confirmed live JSON. |
| Radio Araucana | https://radioaraucana.cl | radio | yes (API locked) | Homepage returns 200 but `/wp-json/...` returns 403. Historic Temuco station (est. 1960, first FM in Chile). Flagged likely not viable, needs closer look. |
| Araucanía Diario | https://araucaniadiario.cl | digital-native | no | `/wp-json/...` returns 404 (bare and `www.`). SIP-affiliated editor per search results; likely custom CMS or different structure — needs closer look. |
| Estación Araucanía | https://estacionaraucania.cl | radio | no | `/wp-json/...` returns 404. New(er) FM station broadcasting in Temuco and Villarrica; likely custom CMS or a schedule-only site with no news content — needs closer look. |
| Malleco Digital | https://www.mallecodigital.cl | digital-native | inconclusive | Domain does not resolve (DNS failure, bare and `www.`, http and https). May be down/moved. |
| RLV / Radio Lago Villarrica | https://www.radiolagovillarrica.cl | radio | inconclusive | Domain does not resolve (DNS failure, bare and `www.`, http and https). May be down/moved. |

## Summary

Found 16 candidate outlets, with real weight outside the regional capital — a notably dense cluster in Angol/Malleco province (6 outlets) and another around Villarrica/Pucón (5 outlets), plus Temuco itself. 11 of the 16 are confirmed WordPress with a live, open REST API — the strongest hit rate of the four regions researched in this batch. One (Radio Araucana) is WordPress but API-locked. Two (Araucanía Diario, Estación Araucanía) are not WordPress, and two (Malleco Digital, RLV) are currently unreachable and worth a manual recheck in phase 2.

## Phase 2 — implemented 2026-08-22

Re-verified all 11 census "yes (API live)" outlets, plus Radio Araucana
("API locked"), live before wiring anything in. Cross-checked `australtemuco`
per `STATUS.md`'s note — it's not in this region's census candidate list at
all (Grupo El Mercurio, already disabled under `regional`), nothing to
reconcile.

**Radio Araucana stays not viable** — `/wp-json/wp/v2/posts` returns
HTTP 403 Forbidden (Cloudflare) even with a browser UA, confirmed live
2026-08-22, matching the census verdict.

**Three census "yes (API live)" outlets turned out not viable on live
re-verification**, each for a different reason:

- **Red Informativa** (`radio.redinformativa.cl`) genuinely has a live,
  responding WP REST API — but `/wp-json/wp/v2/posts` returns `X-WP-Total:
  0`. Checked `/wp-json/wp/v2/types`: the site's real news content lives
  under a JetEngine custom post type (`jet-engine` / "Listing
  Items/Components"), not WordPress's native `post` type. Not an empty
  install, just a non-standard content model the generic
  `WordPressScraper` can't reach — would need a bespoke scraper (the
  `radiopolar.py` class of effort), not judged worth it for one radio
  station in a cluster already covered by Villarrica al Día and Araucanía
  Noticias.
- **Noticias del Lago** (`noticiasdellago.cl`) turned out to be the same
  outlet as Araucanía Noticias under an alias domain — the URL
  301-redirects straight to `araucanianoticias.cl`, confirmed by following
  the redirect to a live `/wp-json/` response. Not a distinct source, not
  registered separately.
- **Pucón Radio** (`puconradio.cl`) is a Next.js frontend
  (`x-powered-by: Next.js`) — `/wp-json/wp/v2/posts` returns an HTML page,
  not JSON, same "SPA swallows the route" pattern as O'Higgins's Rancagua
  TV. No accessible WordPress REST API at the standard path; would need a
  bespoke scraper, not investigated further.

**One census domain had moved**: "Villarrica al Día" was censused at
`villarricaldia.cl`, which now 301-redirects to `vadmedia.cl`. Confirmed
it's the same outlet via `vadmedia.cl`'s own `/wp-json/` `name` field
("Villarrica al dia") before wiring in the new domain directly.

**8 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `araucania` group): **Araucanía Noticias, El Periódico, Malleco
Noticias, Angol Noticias, Las Noticias de Malleco, El Espejo de Malleco,
Malleco 7, Villarrica al Día** (the last under its new `vadmedia.cl`
domain). No `robots.txt` Crawl-delay or wp-json disallow on any of them.
`per_page=100` + full `_embed`/`_fields` timed 3.5-6.4s for all eight — no
`per_page` override needed on any of them, no UA blocking encountered.

Verified with a real `mode=range` test (2026-08-01 to 2026-08-22):
Araucanía Noticias 350, El Periódico 77, Las Noticias de Malleco 88,
Malleco 7 48, Angol Noticias 56, Villarrica al Día 34, El Espejo de
Malleco 27 real recent articles saved cleanly, `seen == saved` on all
seven (no duplicates skipped). Real body text (1.5-5.4KB per article)
confirmed via spot-check; all eight carry a populated `author` field
(several use a shared newsroom byline like "prensa" or "admin" rather than
individual reporter names, which is expected and consistent with several
prior regions).

**Malleco Noticias was dormant-but-real** — `seen=0` on the narrow
recent-range test, but a genuine small archive (`X-WP-Total` 64), just
hadn't published since 2026-05-11 (~3.5 months stale as of this check).
Ran a one-time `mode=full` backfill instead of relying on `mode=update`'s
date math: **64/64 saved cleanly** (2026-02-23 through 2026-05-11, ~5s
total). Left `nightly_enabled` at its default.

`ARCHIVE_STARTS` set to each site's real oldest-indexed post (confirmed
via `?orderby=date&order=asc`, not guessed): Araucanía Noticias
2011-01-28, El Periódico 2025-07-09, Malleco Noticias 2026-02-23, Angol
Noticias 2023-12-29, Las Noticias de Malleco 2022-07-20, El Espejo de
Malleco 2019-11-25, Malleco 7 2019-05-05, Villarrica al Día 2023-05-10.

The 4 census "no"/"inconclusive" outlets (Araucanía Diario, Estación
Araucanía, Malleco Digital, RLV) were left untouched — out of this task's
scope (only "yes (API live)"/"API locked" outlets were re-verified/wired
in this pass).

Araucanía is DONE — both phases complete for the "yes (API live)"/"API
locked" set from the census (8 of 11 census "yes" candidates ended up
viable after re-verification, once the JetEngine/alias-domain/Next.js
cases were caught).
