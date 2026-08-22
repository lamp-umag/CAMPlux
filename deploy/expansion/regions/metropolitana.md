# Región Metropolitana — media census

Researched: 2026-08-22

Scope note: RM is where all the big national outlets happen to be
headquartered (La Tercera, El Mercurio, Emol, CNN Chile, BioBioChile's
national desk, etc.) — those are explicitly out of scope, handled
elsewhere in this project. This file only covers outlets whose actual
editorial focus is Santiago/RM **as a region** — comuna-level or
provincial local news (Cordillera, Maipo, Talagante, Melipilla provinces,
individual comunas like Maipú, Vitacura, Pudahuel, San Bernardo) — not
national politics/business/general-interest coverage that merely happens
to be based in the capital. Duplos was kept despite being fairly
general-interest because it self-identifies as RM-focused ("Noticias de
Chile » Región Metropolitana") and is independent of the big media groups;
it's flagged as borderline below rather than silently excluded.

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Duplos | https://duplos.cl | digital-native | **yes (API live)** | Providencia-based independent outlet; covers politics/business/trends with an RM framing. Borderline general-interest — worth a closer editorial look before committing. |
| El Comunicador | https://elcomunicador.cl | digital-native | **yes (API live)** | Covers Melipilla, Talagante and Maipo provinces. Good scraper candidate. |
| Diario El Labrador | https://diarioellabrador.cl | newspaper | **yes (API live)** | Melipilla, founded 1921. Note: the older `diariolabrador.cl` domain is dead/unreachable — use `diarioellabrador.cl`. |
| Portal de Melipilla | https://www.portaldemelipilla.cl | digital-native | **yes (API live)** | Melipilla province. Good scraper candidate. |
| Puente Alto Al Día | https://puentealtoaldia.com | newspaper (print + digital) | **yes (API live)** | Cordillera province (Puente Alto, Pirque, San José de Maipo). Print since 1962. Good scraper candidate. |
| Puente Altonline | https://puentealtonline.cl | digital-native | **yes (API live)** | Covers Puente Alto, La Florida, San Bernardo. Good scraper candidate. |
| Portal Puente Alto | https://www.portalpuentealto.cl | digital-native | **yes (API live)** | Puente Alto. Good scraper candidate. |
| RedHoy network | https://redhoy.cl | digital-native (multi-comuna network) | **yes (API live)** | Important finding: `hoypuentealto.cl`, `hoy-vitacura.cl`, `hoypudahuel.cl`, and `hoysanbernardo.cl` are NOT four separate outlets — they're comuna-branded domain aliases all pointing at the exact same WordPress backend (`/wp-json/` reports `"name":"RedHoy","url":"https://redhoy.cl"` on every one, and a test post came back byte-identical across all four). Treat as one scrape target, not four. |
| La Voz de Maipú | https://lavozdemaipu.cl | digital-native | **yes (API live, but blocks the default curl User-Agent — returns 403 without one, 200 with a browser-like UA)** | Maipú. Viable, just needs a UA header set in the scraper. |
| La Batalla de Maipú | https://www.labatalla.cl | digital-native | **yes (API live)** | Maipú — politics, police, sports, community news. Good scraper candidate. |
| Noticias del Sol | https://noticiasdelsol.cl | digital-native | **yes (API live)** | Talagante province: Peñaflor, Talagante, Padre Hurtado, El Monte, Isla de Maipo. Good scraper candidate. |
| El Amanecer de lo Herrera | https://delh.cl | digital-native | **yes (API live)** | Maipo province: San Bernardo, Buin, Paine, Calera de Tango. Good scraper candidate. |
| Portal Metropolitano | https://portalmetropolitano.cl | digital-native | **yes (API live)** | Broader RM/zona-central framing — check editorial focus in Phase 2 before treating as purely local. |
| Recoleta al Día | https://www.recoleta.cl/diario-digital-recoleta-al-dia/ | municipal bulletin | not checked | Official municipal government publication, not an independent press outlet — likely low value/out of scope for this project, included only for completeness. |

## Summary

13 candidate independent outlets found (plus one municipal bulletin noted
but not pursued), and it's a strikingly WordPress-heavy region — every
outlet checked came back with a live API except the one not tested. The
standout finding is the **RedHoy network**: four comuna-branded domains
(Puente Alto, Vitacura, Pudahuel, San Bernardo) are all the same
WordPress install, confirmed via matching `/wp-json/` site identity and
identical post content — worth remembering in Phase 2 so effort isn't
wasted building four scrapers for what's really one source. Coverage
clusters heavily south/southwest of the city (Puente Alto/Cordillera,
Maipú, Melipilla, Talagante, Maipo provinces) — comparatively little was
found for the wealthier eastern comunas (Las Condes, Providencia, Ñuñoa,
La Reina) or the northern/western ones (Colina, Lampa, Quilicura, Renca,
Independencia, Recoleta) beyond municipal government sites, which were
deliberately not treated as press. Duplos and Portal Metropolitano are
flagged as borderline general-interest rather than strictly local — a
judgment call to surface for whoever does Phase 2, not resolved here.

## Phase 2 — implemented 2026-08-22

All 13 candidate independent outlets (+ 1 municipal bulletin) were
re-verified live. **12 went live in prod**, 2 were ruled out (Duplos,
Recoleta al Día). This closes out the whole national expansion campaign —
RM was the last of the 15 regions.

### RedHoy resolution

Confirmed live: `hoypuentealto.cl`, `hoy-vitacura.cl`, `hoypudahuel.cl`,
`hoysanbernardo.cl` and `redhoy.cl` all report the identical `/wp-json/`
site identity (`"name":"RedHoy","url":"https://redhoy.cl"`). `redhoy.cl`
was picked as the canonical domain (the one the backend self-identifies
as) — one scraper (`redhoy.py`) covers the whole network, not four.

Two custom REST restrictions were found on RedHoy specifically, both new
failure modes for this project:
1. A plugin (`redhoy/v1` namespace) 403s any `_embed` request from
   anonymous callers (`rh_rest_embed_blocked`) — the plain `/posts`
   endpoint works fine without it. Handled by adding a new `use_embed`
   class flag to `WordPressScraper` itself (default `True`, preserves
   every other source's behavior unchanged) — `redhoy.py` sets
   `use_embed = False`, trading away author/image fields for a working
   scraper.
2. The same plugin caps anonymous pagination at **page 5, regardless of
   `per_page`** (`rh_rest_page_limited`) — confirmed at both `per_page=20`
   and `per_page=100`. This means anonymous access can only ever reach the
   most recent ~500 posts (a rolling ~25-26 day window at RedHoy's
   ~19-20 posts/day pace), never the full archive back to its true oldest
   post (2025-01-01). **`mode=full` will never succeed on this source** —
   it would just 403 through the remaining ~117 of ~122 pages. RedHoy is
   registered and range-tested only (100/406 posts saved in a 3-week
   range test, the rest blocked by the page-5 cap) — same
   register-and-defer posture as `g5noticias` in Valparaíso, but for a
   structural reason (deliberate site-side block) rather than a size/time
   one. `mode=update`'s ~2-day nightly lookback stays comfortably inside
   the reachable window, so nightly updates work fine indefinitely; it's
   only the deep historical backfill that's permanently out of reach
   through the anonymous API.

### Live-verification corrections vs. the census

- **Duplos** — census flagged it borderline; re-verification (15 most
  recent posts, live) confirmed it's actually a national general-interest
  aggregator in practice (celebrity gossip, national SIMCE results,
  national Cadem poll, national security-reform politics, and police
  news from Antofagasta/Osorno/Concepción all in the same feed) — not
  comuna-local RM press. Moved to `DISABLED_SOURCES`.
- **Portal Metropolitano** — also flagged borderline; re-verification (15
  most recent posts) went the other way: consistently comuna/RM-local in
  practice (Maipú youth programs, Las Condes reinsertion program, Barrio
  Italia, GAM, Persa Víctor Manuel, Punto Empleo). Kept in.
- **Puente Altonline** — dormant-but-real: only 70 posts total, last one
  2025-05-22 (~15 months stale as of this check), but real community
  content throughout (not placeholder). Given the tiny size, did a
  one-time `mode=full` backfill instead of range-testing only — 70/70
  saved cleanly.
- **La Voz de Maipú** — census flagged it as blocking the default curl
  User-Agent (403 with no `-A` at all). Re-verified live that this
  project's actual UA (`camplux-Quarry/1.0`, see `base.py`'s `HEADERS`)
  already passes with 200 — the site's rule only blocks a bare/empty UA
  string, not ours specifically. No `use_browser_ua` override needed,
  despite the census note.
- **Portal de Melipilla** — consistently ~16s for `per_page=100` + full
  `_embed`/`_fields` (checked twice) — slower than most of this region
  but comfortably under the 30s timeout, same judgment call as
  `elaconcagua`/`hdn` (~14-15s, no override). Left at default `per_page`.
- **Diario El Labrador** — despite its 1921 print heritage, the digital
  archive only reaches back to 2025-03-07 — the oldest indexed post is a
  "digital edition" PDF-flipbook embed (thin/no real body text after HTML
  stripping), a minority post type mixed into an otherwise normal-article
  feed (verified by sampling 10 recent posts, all real 500-4000 char
  article bodies).

### Rejected

- **Duplos** (`duplos.cl`) — see above; national aggregator in practice,
  out of scope for this campaign despite RM self-framing.
- **Recoleta al Día** — official municipal government bulletin (part of
  `recoleta.cl`), not an independent press outlet. Same exclusion
  criterion applied to municipal sites in other regions. Documented in
  `DISABLED_SOURCES` for completeness, not pursued further.

### Sources live in prod (12)

| source_id | Name | Oldest indexed post | `X-WP-Total` (at check) | Notes |
|---|---|---|---|---|
| `elcomunicador` | El Comunicador | 2025-01-02 | 482 | Melipilla/Talagante/Maipo |
| `diarioellabrador` | Diario El Labrador | 2025-03-07 | 6805 | see digital-edition note above |
| `portaldemelipilla` | Portal de Melipilla | 2017-01-09 | 6670 | ~16s per_page=100, no override |
| `puentealtoaldia` | Puente Alto Al Día | 2024-04-10 | 1301 | Cordillera province |
| `puentealtonline` | Puente Altonline | 2024-06-24 | 70 | dormant since 2025-05-22, one-time `mode=full` (70/70) |
| `portalpuentealto` | Portal Puente Alto | 2002-09-04 | 18303 | deepest archive found in this region |
| `redhoy` | RedHoy | 2025-01-01 | 11722 | `use_embed=False`; anonymous pagination capped at page 5, see above |
| `lavozdemaipu` | La Voz de Maipú | 2009-08-05 | 15888 | census UA-block note doesn't apply to our real UA |
| `labatalla` | La Batalla de Maipú | 2010-04-21 | 6604 | Maipú |
| `noticiasdelsol` | Noticias del Sol | 2023-02-08 | 361 | Talagante province |
| `delh` | El Amanecer de lo Herrera | 2019-09-03 | 3376 | Maipo province |
| `portalmetropolitano` | Portal Metropolitano | 2022-09-05 | 12309 | borderline-but-kept, see above |

All 12 range-tested clean (2026-08-01 to 2026-08-22) with real article
bodies confirmed via direct DB spot-checks except `redhoy` (partial due
to the page-5 cap, documented above) and `puentealtonline` (full
historical backfill instead, since the range fell outside its dormant
window).
