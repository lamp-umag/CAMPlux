# Aysén — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Diario de Aysén | https://diariodeaysen.cl | newspaper (digital) | yes (API live) | `/wp-json/wp/v2/posts` returns real JSON. Coyhaique-based. |
| Diario Aysén | https://diarioaysen.cl | newspaper (digital) | yes (API live) | Distinct domain/outlet from "Diario de Aysén" above — Puerto Aysén based. Confirmed live JSON, not a duplicate. |
| El Divisadero | https://www.eldivisadero.cl | digital-native | no | `/wp-json/...` returns 404. Covers Coyhaique/Aysén Patagonia; archived by Biblioteca Regional de Aysén since 2019. Likely custom CMS — needs closer look in phase 2. |
| Diario Regional Aysén | https://diarioregionalaysen.cl | newspaper (digital) | unknown/custom | Bare domain 301-redirects; following the redirect, the WP probe path resolves to a plain HTML page (`text/html`), not JSON — so not a confirmed live WP REST API even though it may run WP under the hood. Reportedly part of "Grupo DiarioSur," a small regional chain (not a national outlet). |
| Coyhaique Diario | https://coyhaiquediario.cl | digital-native | inconclusive | Domain does not currently resolve (DNS failure on both bare and `www.` variants, http and https). Site may be down, moved, or renamed — worth a manual browser check in phase 2 before writing it off. |
| Canal Sur Patagonia | https://www.canalsurpatagonia.cl | digital-native | yes (API live) | Self-described "medio digital independiente de la Región de Aysén." Confirmed JSON. |
| Radio Santa María | https://www.radiosantamaria.cl | radio | yes (API live) | Region's oldest/most prominent radio station (est. 1979), Coyhaique. Confirmed JSON. |
| Panorámica Aysén | https://www.panoramicaysen.cl | digital-native | no | 301-redirects; following it, probe path returns 404. Not WordPress at that path, or different REST structure — needs closer look. |
| Radio Las Nieves | https://www.rln.cl | radio | yes (API live) | Confirmed JSON. Runs regional news content, not just a station schedule page. |

## Summary

Found 9 candidate outlets for Aysén — a reasonable haul for Chile's least-populous region. 5 of the 9 (Diario de Aysén, Diario Aysén, Canal Sur Patagonia, Radio Santa María, Radio Las Nieves) are confirmed WordPress with a live, open REST API — strong phase-2 candidates. The rest are either not WordPress (El Divisadero, Panorámica Aysén), ambiguous pending a manual look (Diario Regional Aysén — redirects to HTML, not JSON), or currently unreachable (Coyhaique Diario — DNS failure, worth a manual recheck before writing off). No national-outlet bureaus were counted here.

## Phase 2 — implemented 2026-08-22

4 of the 5 confirmed-WP candidates are live in production now (scraper
files in `vault/scrapers/`, registered in `vault/app.py`'s `aysen` source
group): **Diario Aysén, Canal Sur Patagonia, Radio Santa María, Radio Las
Nieves**. Verified with a real `mode=range` test (2026-08-01 to 2026-08-22)
before trusting them: 1 / 119 / 94 / 188 real articles respectively, real
body text confirmed for a sample. `per_page=100` with full `_embed` timed
under 6s for all four — no per-source override needed (contrast with
`ovejeronoticias`'s known slow-host issue).

**Diario de Aysén (diariodeaysen.cl) was ruled out**, despite a "confirmed
live API" in the phase-1 census: `X-WP-Total: 1`, and that one post is
WordPress's own default "Hello World" placeholder — this is a fresh or
under-construction install with no real published content, not an active
outlet. A live API returning valid JSON is necessary but **not sufficient**
— always sanity-check the actual content before trusting a census "yes."
Moved to `DISABLED_SOURCES` in `app.py` with this reason; the scraper file
(`vault/scrapers/diariodeaysen.py`) and registry entry were left in place
(harmless, and if the site publishes real content later, re-enabling it is
a one-line change to `SOURCE_GROUPS["aysen"]["sources"]`).

Aysén is DONE — both phases complete.
