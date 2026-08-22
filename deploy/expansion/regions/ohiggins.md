# O'Higgins — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| El Rancagüino | https://www.elrancaguino.cl | newspaper (print+digital) | yes (API live) | Bare domain redirects to `www.`; confirmed live JSON. Self-described 110-year-old print title covering all 33 communes of the region. |
| El Tipógrafo | https://eltipografo.cl | newspaper/radio | yes (API live) | Confirmed live JSON. Also runs an FM radio (98.9) in Rancagua. |
| Diario El Pulso | https://www.diarioelpulso.cl | digital-native | yes (API live) | Confirmed live JSON. Also runs "Radio El Pulso" online. |
| Rancagua TV | https://www.rancaguatv.cl | digital-native/TV | yes (API live) | Confirmed live JSON. Digital outlet, central-south Chile focus but Rancagua-based. |
| Radio Machalí | https://radiomachali.cl | radio | yes (API live) | Confirmed live JSON. Founded 2018, covers Machalí/Rancagua/region. |
| Diario Rancagua | https://diariorancagua.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. |
| El Rancahuaso | https://www.elrancahuaso.cl | digital-native | no | `/wp-json/...` returns 404 after following redirect. Long-running Rancagua digital outlet; likely custom CMS — needs closer look. |
| HDN Digital | https://hdn.cl | digital-native | yes (API live) | Confirmed live JSON. Covers Santa Cruz, Colchagua province, and the O'Higgins region. |
| Tribuna Colchagua | https://www.latribunadecolchagua.cl | digital-native | yes (API live) | Confirmed live JSON. Covers Colchagua province (San Fernando, Santa Cruz, etc.). |
| Diario Sexta Región Online | https://www.diarioviregion.cl | digital-native | inconclusive | Homepage itself returns 403 (site appears to block automated/curl requests wholesale, likely bot protection) — not a WordPress-specific signal either way. Needs a manual browser check in phase 2. |
| El Marino | https://diarioelmarino.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. Founded 2013, covers Cardenal Caro province (Pichilemu area). |
| PichilemuNews | https://www.pichilemunews.cl | digital-native | yes (API locked) | Homepage 301s; `/wp-json/...` returns 403. Flagged likely not viable, needs closer look. |
| PichilemuTV | https://pichilemutv.org | digital-native/TV | yes (API live) | Confirmed live JSON, active recent posts. |
| Radio Santa Cruz | https://santacruzfm.cl | radio | yes (API live) | Confirmed live JSON. Has a dedicated `/noticias/` section on-site too. |

## Summary

Found 14 candidate outlets spread across Rancagua/Cachapoal, Colchagua (San Fernando/Santa Cruz), and Cardenal Caro (Pichilemu) provinces — good province-wide coverage, not just the regional capital. 11 of the 14 are confirmed WordPress with a live, open REST API (El Rancagüino, El Tipógrafo, Diario El Pulso, Rancagua TV, Radio Machalí, Diario Rancagua, HDN Digital, Tribuna Colchagua, El Marino, PichilemuTV, Radio Santa Cruz) — an unusually strong phase-2 haul for a mid-size region. One (PichilemuNews) is WordPress but API-locked. El Rancahuaso is not WordPress (needs closer look), and Diario Sexta Región Online blocks automated requests entirely so its CMS is unconfirmed.

## Phase 2 — implemented 2026-08-22

Re-verified all 11 census "yes (API live)" outlets live before wiring
anything in.

**Two of the census "yes (API live)" outlets turned out to be false
positives** on live re-verification: **El Tipógrafo** is actually an
Angular SPA served from AWS API Gateway/CloudFront (`ng-version` in the
HTML, `x-powered-by: Express`), not WordPress — `/wp-json/` returns the
same HTML shell as every other route. **Rancagua TV** returns HTML (200,
`text/html`) at `/wp-json/wp/v2/posts` too, no `wp-content` markers
anywhere on the site. Both documented in `DISABLED_SOURCES`, no scraper
file.

**PichilemuNews stays not viable** — confirmed live 2026-08-22:
`/wp-json/wp/v2/posts` returns HTTP 403 "No tienes autorización para
llevar a cabo esta acción" (WordPress's own REST-API-disabled error page),
matching the census's "API locked" verdict.

**Diario Sexta Región Online (diarioviregion.cl), census "inconclusive",
was also checked and ruled out** — it's actually Joomla (`/media/jui/`
paths, Joomla's bundled jQuery UI), fronted by Cloudflare, which blocks
every request outright with a "Malware detected" 403 before any content
route is reachable. Not WordPress, not viable either way.

**9 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `ohiggins` group): **El Rancagüino, Diario El Pulso, Radio
Machalí, Diario Rancagua, HDN Digital, Tribuna Colchagua, El Marino,
PichilemuTV, Radio Santa Cruz**.

- **HDN Digital** has `Crawl-Delay: 10` in `robots.txt` — `min_delay =
  10.0`, same treatment as Ovalle Hoy / Periódico Los Ríos.
- **Diario Rancagua**'s host can't resolve `_embed` for a full 100-post
  page within the 30s request timeout — `per_page=100` consistently ~35s
  (over budget), `per_page=50` ~20.6s (too close to trust), `per_page=25`
  a reliable ~9.8s (checked twice). Same class as ovejeronoticias/
  iquiquealdia — `per_page=25` override applied.
- **El Rancagüino**'s WAF blocks both our default camplux-Quarry UA and
  the shared `BROWSER_UA` (Chrome/120-Mac) with a 403 — confirmed live via
  an app-side test that came back `seen=0/saved=0` with HTTP 403 in the
  logs despite manual curl working fine. Same class as `madero.py`: a
  plain Chrome/126-Windows UA passes reliably. Per-source `__init__`
  override added, same pattern as `madero.py`.
- The other six had no disqualifying `robots.txt` restriction and no UA
  blocking; `per_page=100` + full `_embed`/`_fields` timed 3.1-14.5s.

Verified with a real `mode=range` test (2026-08-01 to 2026-08-22): El
Rancagüino 619 (after the UA fix), Diario El Pulso 179, Diario Rancagua
89, Tribuna Colchagua 24, El Marino 39, PichilemuTV 33, Radio Santa Cruz
30, HDN Digital 5, Radio Machalí 1 real recent articles saved cleanly, all
`seen == saved` (no duplicates skipped). Real body text (0.6-8.3KB per
article) confirmed via spot-check; El Rancagüino, Diario El Pulso, Diario
Rancagua, HDN Digital, Tribuna Colchagua, PichilemuTV, and Radio Machalí
all carry real author/byline fields out of the box (El Marino and Radio
Santa Cruz don't populate a WP author name, same as several prior
regions' sources).

**Radio Machalí has a genuinely thin archive** (`X-WP-Total` 33, oldest
indexed post 2026-03-31) — real, distinct recent headlines rather than a
theme-demo placeholder, just a small/newer publisher. Registered normally,
no special handling needed.

**El Marino's `ARCHIVE_STARTS` is 1907-08-18**, not a typo — its oldest
indexed posts are a real digitized historical-newspaper collection (five
sequential posts all timestamped `1907-08-18T01:0x:xx`, clearly a batch
import), distinct from the single-post data-entry-typo pattern seen in
`laserenaonline`/`noticiaslosrios`. Used as the real archive start.

`ARCHIVE_STARTS` set to each site's real oldest-indexed post (confirmed
via `?orderby=date&order=asc`, not guessed): El Rancagüino 2009-10-01,
Diario El Pulso 2019-09-01, Radio Machalí 2026-03-31, Diario Rancagua
2013-10-31, HDN Digital 2015-09-05, Tribuna Colchagua 2023-01-04, El
Marino 1907-08-18, PichilemuTV 2008-04-29, Radio Santa Cruz 2021-10-08.

El Rancahuaso (census "no") was left untouched, and additionally
documented in `DISABLED_SOURCES` for completeness alongside the other
findings from this pass, since it was already re-checked as part of the
same live sweep.

O'Higgins is DONE — both phases complete for the "yes (API live)"/"API
locked" set from the census (9 of 11 census "yes" candidates ended up
viable after re-verification, once the two false positives were caught).
