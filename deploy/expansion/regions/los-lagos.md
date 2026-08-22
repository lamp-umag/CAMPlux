# Los Lagos — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Diario Digital Los Lagos | https://diarioloslagos.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. Covers Puerto Montt/Llanquihue and region-wide. |
| El Llanquihue | https://www.ellanquihue.cl | newspaper (print+digital) | no (API dead) | Part of "Grupo DiarioSur" (small regional chain, El Mercurio-adjacent but distinctly regional print title, ~1970s founding). **Correction (resolved 2026-08-22, see Phase 2 note below): `llanquihue.cl` (no "el" prefix, the domain originally listed here) is a DIFFERENT organization — the Municipalidad de Llanquihue's official government site, confirmed via its own `/wp-json/` `name` field. The actual newspaper's real domain, `www.ellanquihue.cl`, has a dead WP REST API (404).** Not a domain-confusion mystery, just two unrelated sites sharing a name. |
| Diario Laguino | https://www.diariolaguino.cl | digital-native | yes (API live) | Bare domain redirects to `www.`; following it, confirmed live JSON. |
| Diario de Osorno | https://www.diariodeosorno.cl | newspaper (print+digital) | yes (API live) | Bare domain redirects to `www.`; confirmed live JSON. Long-running Osorno print title. |
| ChiloeNews | https://chiloenews.cl | digital-native | yes (API live) | Confirmed live JSON, active recent posts. Independent Chiloé outlet. |
| La Opinión de Chiloé | https://laopiniondechiloe.cl | digital-native | yes (API live) | Confirmed live JSON. |
| Diario Puerto Varas | https://diariopuertovaras.cl | digital-native | yes (API live) | Confirmed live JSON, active recent posts. Self-described community-focused outlet. |
| Radio Frutillar FM 96.7 | https://radiofrutillarfm.cl | radio | yes (API live) | Confirmed live JSON. Covers Frutillar/Llanquihue/Puerto Octay lake basin. |
| Radio Sago (Osorno) | https://radiosago.cl | radio | yes (API locked) | Homepage 301s; `/wp-json/...` returns 401. Flagged likely not viable, needs closer look in phase 2. |
| La Voz del Archipiélago | https://www.lavozdelarchipielago.cl | digital-native | no | `/wp-json/...` returns 404 (bare and `www.`, both http/https). Chiloé-focused, covers whole archipelago. Not WordPress or different URL structure — needs closer look. |
| Radio Chiloé | https://www.radiochiloe.cl | radio | no | `/wp-json/...` returns 404 (bare and `www.`). Historic Castro station (est. 1962, 1030 AM), has a news section on-site but likely custom/legacy CMS. |
| El Queilen | https://elqueilen.cl | digital-native | inconclusive | Domain does not resolve (DNS failure, bare and `www.`, http and https). Site may be down/moved — worth a manual browser check in phase 2. |
| InterradioTV (Frutillar) | https://www.interradiotv.cl | radio | no | `/wp-json/...` returns 404 after following redirect. Has a news/coverage section; likely custom CMS. |

## Summary

Found 13 candidate outlets across the region (Puerto Montt/Llanquihue, Osorno, Chiloé, Puerto Varas/Frutillar) — good spread beyond just the regional capital. 8 of the 13 are confirmed WordPress with a live, open REST API (Diario Digital Los Lagos, El Llanquihue, Diario Laguino, Diario de Osorno, ChiloeNews, La Opinión de Chiloé, Diario Puerto Varas, Radio Frutillar FM) — a strong phase-2 haul. One (Radio Sago) is WordPress but API-locked. Three (La Voz del Archipiélago, Radio Chiloé, InterradioTV) are not WordPress or use a different structure, and one (El Queilen) is currently unreachable. Note: an external study (Fundación Gabo "Desiertos de Noticias Locales") flags roughly half of this region's communes as local-news deserts, consistent with coverage concentrating around Puerto Montt, Osorno, and Chiloé rather than being evenly spread.

## Pre-resolved finding (2026-08-22, ahead of this region's own Phase 2 pass)

The "El Llanquihue" domain-confusion flagged in `STATUS.md` is resolved:
`llanquihue.cl` (the domain originally recorded above) is the
**Municipalidad de Llanquihue**'s official government site, not the
newspaper — confirmed via its own `/wp-json/` endpoint's `name` field
("Municipalidad de Llanquihue"). Two unrelated organizations sharing a
similar name, not one confusing entity. The actual newspaper's real
domain, `www.ellanquihue.cl`, has a dead WP REST API (`/wp-json/wp/v2/posts`
returns 404 even with a browser UA) — genuinely not viable via the normal
WP path right now, not a mystery to solve, just not currently scrapable.
Whoever runs this region's full Phase 2 pass: skip `ellanquihue` (already
coded at `vault/scrapers/ellanquihue.py` from an earlier, unrelated
session, but pointed at the dead domain) rather than re-investigating it —
this note is the investigation.

## Phase 2 — implemented 2026-08-22

Re-verified every census "yes (API live)" outlet live before wiring
anything in (skipped `ellanquihue` per the pre-resolved finding above, and
re-checked Radio Sago per `STATUS.md`'s note rather than trusting the
census "WP-locked" verdict blindly).

**Census correction found during re-verification**: "Diario Laguino"
(`diariolaguino.cl`) is **not actually a Los Lagos region outlet** — it's
the exact same domain already investigated and disabled under the
`los_rios` region's `DISABLED_SOURCES` entry (part of the non-WordPress
"Diario Futrono network" cluster). "Los Lagos" here refers to a *comuna*
near Valdivia in the Los Ríos region, not this region — the census
researcher picked it up under the wrong region due to the shared name.
Not re-added here; see `app.py`'s `los_rios` `DISABLED_SOURCES` block for
the original finding.

**Diario de Osorno was ruled out post-census** — `/wp-json/` returns the
homepage HTML (200, `text/html`), not JSON. It's the same proprietary
"Grupo DiarioSur" CMS as El Llanquihue (`masmedioschile.cl` templating,
confirmed via page source), not WordPress at all despite the census
marking it "yes (API live)". Documented in `DISABLED_SOURCES`.

**Radio Sago stays not viable** — `/wp-json/wp/v2/posts` returns HTTP 401
`rest_login_required` even with a browser UA, confirmed live 2026-08-22.
Documented in `DISABLED_SOURCES`.

**5 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `los_lagos` group): **Diario Digital Los Lagos, ChiloeNews, La
Opinión de Chiloé, Diario Puerto Varas, Radio Frutillar FM 96.7**. No
`robots.txt` Crawl-delay or wp-json disallow on any of them. `per_page=100`
+ full `_embed`/`_fields` timed 4.9-15.1s for all five (ChiloeNews slowest
at 15.1s, likely Cloudflare overhead, still comfortably inside the 30s
request timeout) — no `per_page` override needed on any of them, no UA
blocking encountered.

Verified with a real `mode=range` test (2026-08-01 to 2026-08-22): Diario
Digital Los Lagos 63, ChiloeNews 50, Diario Puerto Varas 36, Radio
Frutillar FM 3 real recent articles saved cleanly, `seen == saved` on all
four (no duplicates skipped). Real body text (1.0-4.5KB per article)
confirmed via spot-check; Diario Digital Los Lagos, ChiloeNews, and Radio
Frutillar FM carry real author bylines out of the box.

**La Opinión de Chiloé was dormant-but-real** — `seen=0` on the narrow
recent-range test, but a genuine historical archive (`X-WP-Total` 5848),
just hadn't published since 2026-07-19 (~1 month stale as of this check).
Ran a one-time `mode=full` backfill instead of relying on `mode=update`'s
date math: **5848/5848 saved cleanly** (2015-02-08 through 2026-07-19,
~227s total). Body text confirmed real (10.2KB per article, author field
falls back to the outlet's own name rather than a byline). Left
`nightly_enabled` at its default — a month-scale gap, not an unbounded
pathological one.

`ARCHIVE_STARTS` set to each site's real oldest-indexed post (confirmed
via `?orderby=date&order=asc`, not guessed): Diario Digital Los Lagos
2025-10-06, ChiloeNews 2021-06-01, La Opinión de Chiloé 2015-02-08, Diario
Puerto Varas 2017-10-18, Radio Frutillar FM 2023-07-20.

The 4 census "no"/"inconclusive" outlets (La Voz del Archipiélago, Radio
Chiloé, El Queilen, InterradioTV) were left untouched — out of this task's
scope (only "yes (API live)" outlets were re-verified/wired in this pass).

Los Lagos is DONE — both phases complete for the "yes (API live)" set from
the census (net: 5 of the 7 non-`ellanquihue` "yes (API live)" candidates
turned out viable after re-verification, once the Diario Laguino
misattribution and Diario de Osorno false positive were caught).
