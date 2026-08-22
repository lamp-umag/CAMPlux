# Coquimbo — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| El Observatodo | https://www.elobservatodo.cl | digital-native | no / unknown | La Serena/Coquimbo digital outlet, appears to be one of the bigger regional players. Root loads (200), zero WP markers, wp-json 404 — likely non-WP. |
| Ovalle Hoy | https://ovallehoy.cl | digital-native (comuna) | yes (API live) | Ovalle-focused digital daily. |
| La Serena Online | https://laserenaonline.cl | digital-native | yes (API live) | Covers La Serena, Coquimbo, Ovalle, Illapel, Vicuña and more. |
| El Coquimbano | https://www.elcoquimbano.cl | digital-native (comuna) | yes (API live) | One of Agencia Caracol's ~4 Coquimbo-region digital papers. |
| El Illapelino | https://www.elillapelino.cl | digital-native (comuna) | yes (API live) | "Diario Electrónico de Illapel", covers Choapa province. |
| Diario Choapa | https://diariochoapa.cl | digital-native (province) | yes (API live) | Covers Illapel, Los Vilos, Salamanca, Canela (Choapa province). |
| Diario El Día | https://www.diarioeldia.cl | newspaper (digital) | no / unknown | The region's historic daily (founded 1944, La Serena), ~55k daily readers as of 2015. Root loads (200), zero WP markers, wp-json 404 — looks like a custom/proprietary CMS, not WordPress. |
| Diario Regional (Coquimbo/La Serena/Ovalle/Illapel) | https://www.diarioregional.cl | digital-native | unknown / connection error | Both plain curl and a browser-UA retry timed out completely — inconclusive, possibly a dead/dormant domain. |
| Radio Riquelme | https://radioriquelme.cl | radio (news site) | yes (API live) | 1350 AM, "Desde el Corazón de Coquimbo", covers La Serena/Coquimbo/rural Elqui & Limarí. |
| Mi Radio LS | https://www.miradiols.cl | radio (news site) | yes (API live) | Multi-frequency network across La Serena/Coquimbo, Vicuña, Paihuano and other communes. |

## Summary

10 outlets found, solidly in the expected range for a region of ~833k people. 7 of 10 are confirmed WordPress with a live open API, including a strong cluster of comuna/province-level outlets (Ovalle, Illapel/Choapa, and the Agencia Caracol network) — a good set of near-zero-effort phase-2 candidates. The region's two most established legacy papers (El Día and El Observatodo) both look non-WordPress and will need custom scraping if pursued. Diario Regional is a dead end for now — completely unreachable, not just API-blocked.

## Phase 2 — implemented 2026-08-22

Re-verified all 7 census "yes (API live)" outlets live before wiring anything
in.

**Mi Radio LS (miradiols.cl) was ruled out** — its `robots.txt` explicitly
has `Disallow: /wp-json/` under a `User-agent: *` block (Yoast-managed), on
top of a separate Cloudflare-managed AI-crawler block section. The REST API
itself does respond if you ignore robots.txt, but the site has clearly and
deliberately opted out of exactly the path this project needs — same
disqualifying category as `elmagallanews`'s Crawl-delay, just expressed as
an explicit path disallow instead. Documented in `DISABLED_SOURCES`
(`app.py`, region `coquimbo`), no scraper file.

**6 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `coquimbo` group): **Ovalle Hoy, La Serena Online, El
Coquimbano, El Illapelino, Diario Choapa, Radio Riquelme**. Ovalle Hoy has
`Crawl-Delay: 20` in `robots.txt` — set `min_delay = 20.0` on its scraper,
same treatment as Periódico Los Ríos's `Crawl-Delay: 10` precedent, still
well within reason. The other five had no disqualifying `robots.txt`
restriction. `per_page=100` + full `_embed`/`_fields` timed 3.5-5.6s for
all six — no `per_page` override needed, no UA blocking encountered.

Verified with a real `mode=range` test (2026-08-01 to 2026-08-22): Ovalle
Hoy 106, La Serena Online 283, El Coquimbano 47, El Illapelino 19, Radio
Riquelme 128 real recent articles saved cleanly, all `seen == saved` (no
duplicates skipped). Real body text (1.3-6.3KB per article) confirmed via
spot-check; Ovalle Hoy, La Serena Online, Diario Choapa, and Radio Riquelme
all carry real author bylines out of the box.

La Serena Online has one single data-entry-typo post (`0027-10-22` instead
of a real date, "Familias de sector Parte Alta de Coquimbo…") — used the
site's real oldest post (2015-08-10) for `ARCHIVE_STARTS` instead, same
handling as the `noticiaslosrios` precedent. Noted in the scraper's own
docstring.

**Diario Choapa was dormant-but-real** (same pattern as Cappissima
Multimedial / Los Ríos al Día) — `seen=0` on the narrow recent-range test,
but a genuine historical archive (`X-WP-Total` 1189), just stopped
publishing recently (newest indexed post was 2026-03-05, ~5.5 months stale
as of today 2026-08-22). Ran a one-time `mode=full` backfill instead of
relying on `mode=update`'s date math: **1189/1189 saved cleanly**
(2021-07-17 through 2026-03-05, ~35s total). Left `nightly_enabled` at its
default — a slow-dormancy gap, not an unbounded pathological one.

`ARCHIVE_STARTS` set to each site's real oldest-indexed post (confirmed via
`?orderby=date&order=asc`, not guessed, except La Serena Online's typo case
above): Ovalle Hoy 2014-07-19, La Serena Online 2015-08-10, El Coquimbano
2020-08-20, El Illapelino 2020-11-02, Diario Choapa 2021-07-17, Radio
Riquelme 2019-01-29.

The 3 census "no/unknown"/"unreachable" outlets (El Observatodo, Diario El
Día, Diario Regional) were left untouched — out of this task's scope (only
"yes (API live)" outlets were re-verified/wired in this pass).

Coquimbo is DONE — both phases complete for the "yes (API live)" set from
the census.
