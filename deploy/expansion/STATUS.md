# Expansion status — live tracker

Read `PLAN.md` first if you haven't. This file is the source of truth for
"where are we right now" — update it as work happens, don't let it drift.

Last updated: 2026-08-22 (all 15 regions censused AND implemented — **the
national expansion campaign is complete**. Aysén, Arica y Parinacota,
Atacama, Tarapacá, Los Ríos, Ñuble, Antofagasta, Coquimbo, Los Lagos,
O'Higgins, Araucanía, Maule, Biobío, Valparaíso, Región Metropolitana all
fully implemented)

**Operational note:** rebuilding the `vault` container (`docker compose
build vault && docker compose up -d vault`, needed after every scraper/
app.py change since source isn't bind-mounted) kills any in-flight request
`ovejero_gapfill.py` has open — confirmed twice in a row (2026-08-22
~09:15, ~09:21), no data loss (INSERT OR IGNORE + it only marks a year
"complete" after a clean finish) but wastes whatever's left of that
session's 5.5h window. Given how many rebuilds this expansion project
needs, **batch several sources/regions per rebuild rather than rebuilding
after every single one**, and only relaunch `ovejero_gapfill.py --now` at
a natural break point (end of a work session / long gap between rebuilds),
not immediately after every interruption.

**Important reconciliation found mid-project (2026-08-22):** `vault/scrapers/__init__.py`
already had a MORE COMPLETE registry (`GROUPS`/`_SCRAPERS`) than `vault/app.py`'s
own hand-written `SOURCE_GROUPS` — includes fully-coded-but-never-wired-in
scrapers from an earlier, undocumented session, including **El Llanquihue
(`ellanquihue`) for Los Lagos** (already works, just needs `app.py` synced to
expose it), plus disabled-but-documented entries `elsur` (Biobío),
`australtemuco` (Araucanía), `mercuriovalpo` (Valparaíso), and several extra
nacional sources (`eldinamo`, `exante`, `interferencia`, `eldesconcierto`).
See `PLAN.md`'s reconciliation note (being added) before assuming a region
starts from zero — check `vault/scrapers/__init__.py`'s `GROUPS` dict first.

| Region | Phase 1 (census) | Phase 2 (test/implement) | Outlets found | Viable | Notes |
|---|---|---|---|---|---|
| Aysén | done | **DONE** | 9 | 5 confirmed, 4 live in prod | see `regions/aysen.md` — `diariodeaysen` ruled out post-census (empty WP install, only the "Hello World" placeholder post — API being live isn't enough, always check real content) |
| Arica y Parinacota | done | **DONE** | 7 | 4 confirmed, all 4 live in prod | see `regions/arica-y-parinacota.md`; Cappissima Multimedial got a one-time `mode=full` instead (real content, but dormant since ~Nov 2025) |
| Atacama | done | **DONE** | 8 (+1 defunct, documented) | 6 confirmed WP, all 6 live in prod | see `regions/atacama.md`; `madero` needed a per-source UA override (WAF blocks default + shared BROWSER_UA, plain Chrome/126-Windows UA passes) |
| Tarapacá | done | **DONE** | 7 | 5 confirmed WP, all 5 live in prod | see `regions/tarapaca.md`; RTC/CORMUDESI's shared-domain caveat resolved cleanly (whole posts endpoint is already just RTC content); `iquiquealdia` needed `per_page=25` override (slow host, same class as ovejeronoticias) |
| Los Ríos | done | **DONE** | 19 | 6 confirmed WP live in prod (census overcounted -- 10 "confirmed WP" domains turned out NOT WordPress on re-verification, see below) | see `regions/los-rios.md`; **census correction**: the "Diario Futrono network" (9 domains) + Diario de Valdivia all 404/HTML on wp-json despite census "yes (API live)" -- not WordPress, moved to `DISABLED_SOURCES`; `noticiasriobueno` also disabled (Crawl-delay 3600s); `losriosaldia`+`periodicolosrios` were dormant-but-real (one-time `mode=full` backfill) |
| Ñuble | done | **DONE** | 11 | 8 confirmed WP, 6 live in prod | see `regions/nuble.md`; `orbitanoticias` ruled out post-census (whole server returns empty 200 bodies, not just wp-json); `ladiscusion` is Ñuble's outlet but was already registered pre-campaign under the `regional` group, left as-is |
| Antofagasta | done | **DONE** | 8 | 4 confirmed WP, 3 live in prod | see `regions/antofagasta.md`; thinnest region so far, genuinely smaller press landscape; `nuevonortefm` ruled out post-census (WP theme-demo placeholder content, never real news) |
| Coquimbo | done | **DONE** | 10 | 7 confirmed WP, 6 live in prod | see `regions/coquimbo.md`; `miradiols` ruled out post-census (robots.txt explicitly disallows /wp-json/); `ovallehoy` needed `min_delay=20` (Crawl-delay 20s); `diariochoapa` was dormant-but-real (one-time `mode=full`, 1189/1189); `laserenaonline` has one data-entry-typo post ("0027"), real oldest used instead |
| Los Lagos | done | **DONE** | 13 | 5 confirmed WP, all 5 live in prod | see `regions/los-lagos.md`; `ellanquihue` skipped per pre-resolved finding (dead API); census correction: "Diario Laguino" is actually a Los Ríos-region outlet (already disabled there), not Los Lagos; `diariodeosorno` ruled out post-census (not WordPress, `/wp-json/` returns homepage HTML — same proprietary "Grupo DiarioSur" CMS as El Llanquihue); `radiosago` stays not viable (401 `rest_login_required`); `laopiniondechiloe` was dormant-but-real (one-time `mode=full`, 5848/5848) |
| O'Higgins | done | **DONE** | 14 | 9 confirmed WP live in prod | see `regions/ohiggins.md`; `eltipografo` (Angular SPA, not WP) and `rancaguatv` (HTML shell, not WP) ruled out post-census despite "API live"; `pichilemunews` stays not viable (403, REST disabled); `diarioviregion` also ruled out (Joomla, Cloudflare-blocked); `elrancaguino` needed a per-source UA override (WAF blocks default + shared BROWSER_UA, plain Chrome/126-Windows UA passes, same as `madero`); `diariorancagua` needed `per_page=25` (slow host); `hdn` needed `min_delay=10` (Crawl-delay 10s) |
| Araucanía | done | **DONE** | 16 | 8 confirmed WP live in prod | see `regions/araucania.md`; note `australtemuco` already disabled+documented in code (Grupo El Mercurio, proprietary CMS) — cross-check census entry matches (not in this region's candidate list at all, nothing to reconcile); `radioaraucana` stays not viable (403); `redinformativa` ruled out (real content lives under a JetEngine custom post type, not native WP posts); `noticiasdellago` ruled out (redirects to `araucanianoticias`, same outlet); `puconradio` ruled out (Next.js frontend, no WP REST at standard path); `villarricaldia` domain moved to `vadmedia.cl`; `malleconoticias` was dormant-but-real (one-time `mode=full`, 64/64) |
| Maule | done | **DONE** | 15 | 9 confirmed WP live in prod | see `regions/maule.md`; `tv5` ruled out post-census (Next.js frontend, not WP); Talca/Linares/Cauquenes share a network launch post ("Red de Diarios del Maule") but each has its own distinct large archive; `cauquenesnet` has a genuine digitized archive back to 2000; `radiochilenadelmaule` was dormant-but-real (one-time `mode=full`, 31/31) |
| Biobío | done | **DONE** | 18 (17 + 1 defunct) | 4 confirmed WP live in prod | see `regions/biobio.md`; `elsur` already disabled+documented in code (matches census finding, region field fixed to `biobio`); `radiollacolen` ruled out post-census (empty WP install, X-WP-Total 0, no custom post type either); Sur Actual / Radio El Carbón still down on recheck, left inconclusive |
| Valparaíso | done | **DONE** | 16 | 6 confirmed WP live in prod | see `regions/valparaiso.md`; `mercuriovalpo` already disabled+documented in code (matches census finding, region field fixed to `valparaiso`); `portalesfm` ruled out post-census (WP API live but posts are a song-play log, not news); `g5noticias` has a huge 218,838-post archive, not yet fully backfilled |
| Región Metropolitana | done | **DONE** | 13 (+1 municipal, excluded) | 12 confirmed WP live in prod | see `regions/metropolitana.md`; **RedHoy resolved as one canonical scraper** (`redhoy.cl`, covers hoypuentealto/hoy-vitacura/hoypudahuel/hoysanbernardo too — confirmed byte-identical backend); RedHoy also has two custom anti-scraping restrictions never seen before in this project — `_embed` 403s for anonymous callers (new `use_embed=False` flag added to `WordPressScraper`) and anonymous pagination hard-capped at page 5 regardless of `per_page` (~500 most recent posts reachable, full historical `mode=full` permanently impossible via the anonymous API) — registered and range-tested only, nightly `mode=update` unaffected; `duplos` ruled out post-census (national aggregator in practice despite RM framing); `recoletaaldia` excluded (municipal bulletin, not independent press); `puentealtonline` was dormant-but-real (one-time `mode=full`, 70/70) |

## Phase 1 (census) is complete for all 15 regions.

Magallanes is not listed in the table above — it's already fully
developed, tracked in the main `project_camplux.md` memory, not part of
this campaign.

## Next action

**None — the campaign is complete.** Phase 2 is done for all 15 regions
(Aysén, Arica y Parinacota, Atacama, Tarapacá, Los Ríos, Ñuble,
Antofagasta, Coquimbo, Los Lagos, O'Higgins, Araucanía, Maule, Biobío,
Valparaíso, Región Metropolitana), plus Magallanes which was already
fully developed before this campaign started. Anyone picking this project
up now is doing *maintenance* (nightly rotation health, occasional
re-verification of a source that's gone stale/dead, `ovejero_gapfill.py`'s
own separate concern), not new-region expansion — there are no more
regions left to add.

## Campaign closed — final tally (2026-08-22)

- **15/15 regions** implemented (Aysén → Región Metropolitana, smallest
  to biggest population, as planned in `PLAN.md`), plus Magallanes
  (pre-existing, 11 sources, not counted below).
- **93 new sources** added across the 15 expansion regions (per-region
  breakdown is in the table above) — on top of Magallanes' pre-existing
  11, nacional's ~16, and a handful of legacy "regional"/"internacional"
  sources. Total sources tracked by the running app (`/status`) as of
  this close-out: **111**.
- **~568,000 article rows** across every source's DB combined (568,479
  exactly, via `/status` on 2026-08-22 — this number keeps growing nightly
  through the update rotation and isn't a final/frozen figure, just a
  snapshot at campaign close).
- One deliberate register-and-defer left open by design, not by mistake:
  `g5noticias` (Valparaíso, 218,838-post archive, too large to backfill
  in one sitting) and `redhoy` (RM, anonymous API pagination hard-capped
  by the site itself at ~500 most recent posts — full historical
  backfill isn't deferred, it's structurally impossible via the public
  API). Both are live and range-tested, both keep updating nightly, both
  are just missing deep history.
- Everything else registered in this campaign either has a full
  historical backfill already done, or was small enough that its first
  `mode=full`/range test already captured its whole practical archive.
- See each `regions/<slug>.md` file for the full outlet-by-outlet
  reasoning, and `vault/app.py`'s `DISABLED_SOURCES` for every outlet
  that was checked and rejected, with why.
