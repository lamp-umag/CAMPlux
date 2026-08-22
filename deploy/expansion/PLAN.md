# camplux national expansion — master plan

**Started:** 2026-08-22. **Status:** Phase 1 (census) in progress.
**If you are a fresh agent picking this up cold, read this whole file
before touching anything.** It's written to be self-contained.

## The ask (paraphrased from the user, 2026-08-22)

camplux currently has one region — Magallanes — well developed (11 sources,
most with author fields, image backfill, search/explorer, nightly
incremental updates). The user wants that same *level of infrastructure*
extended to **every one of Chile's 16 regions**, going region by region,
smallest population to biggest, explicitly accepting that we won't fully
scrape every source on day one — the goal is building out the same kind of
foundation (a census of outlets, a scrapability verdict on each, working
scrapers for the viable ones, registered in the app) everywhere, not
just Magallanes forever. Explicit instructions: don't break the existing
dataset (**backed up first, see below**), keep a running documentation
trail accessible from the app's own UI (not just buried in this repo), and
write this plan assuming it will span multiple sessions / possibly a fresh
agent with no memory of this conversation.

## Safety — read this before writing any code

A full, consistent backup of every existing source DB (18 sources, ~2.1GB)
was taken **before this project started**, at
`/home/mnx/camplux_backups/2026-08-22_pre-expansion.tar.gz`
(SHA256 in the sibling `.sha256` file; uncompressed copy + manifest also
sitting in `/home/mnx/camplux_backups/2026-08-22_pre-expansion/`, with its
own README explaining exactly how to restore). If anything in this project
looks like it damaged the existing Magallanes/nacional dataset, restore
from there — full instructions are in that README, don't wing it.
**Take a fresh backup again if a lot of new work has landed and you're
about to do something risky (bulk schema change, mass re-scrape, etc.)** —
the same one-liner is in that README's "how" section, adapt the date.

## The 16 regions, smallest → biggest (Censo 2024, INE — verified live via
Wikipedia's "Anexo:Regiones de Chile por población", 2026-08-22)

| # | Region | Population | Status |
|---|---|---|---|
| 1 | Aysén | 100,745 | not started |
| — | *Magallanes y la Antártica Chilena* | *166,537* | **already done** (11 sources, see main project memory) |
| 2 | Arica y Parinacota | 244,569 | not started |
| 3 | Atacama | 299,180 | not started |
| 4 | Tarapacá | 369,806 | not started |
| 5 | Los Ríos | 398,230 | not started |
| 6 | Ñuble | 512,289 | not started |
| 7 | Antofagasta | 635,416 | not started |
| 8 | Coquimbo | 832,864 | not started |
| 9 | Los Lagos | 890,284 | not started |
| 10 | O'Higgins | 987,228 | not started |
| 11 | Araucanía | 1,010,423 | not started |
| 12 | Maule | 1,123,008 | not started |
| 13 | Biobío | 1,613,059 | not started |
| 14 | Valparaíso | 1,896,053 | not started |
| 15 | Región Metropolitana | 7,400,741 | not started |

Work smallest-first (Aysén next, RM last) — smaller regions have fewer
outlets to census/test, so this gives quick, complete wins early rather
than getting stuck partway through a huge region for days. **Live status
lives in `STATUS.md` in this directory, not in this table** — update that
file as work happens, this table is the static reference plan.

## Two phases, per the user's own framing

**Phase 1 — census.** For each region, find its real written/broadcast
media outlets with an online presence: regional newspapers, radio station
news sites, local TV, digital-native regional outlets. Aim for genuine
regional/local press, not national outlets that happen to cover the region
(BioBioChile, national TV, etc. are already handled separately as
"nacional" sources — see `vault/app.py`'s `SOURCE_GROUPS`). Search results,
the region's own Wikipedia page ("Medios de comunicación" section if
present), and directories of Chilean regional press are all fair game.
Aim for real coverage, not just the first 2-3 results — most regions have
somewhere between 5 and 20 identifiable outlets worth at least checking.
Output: one file per region at `deploy/expansion/regions/<slug>.md` (slug
= lowercase, no accents/spaces, e.g. `los-rios.md`, `arica-y-parinacota.md`)
listing every candidate outlet found: name, URL, type (newspaper/radio/TV/
digital-native), and a first-pass guess at whether it looks WordPress-based
(a quick `curl -s <url>/wp-json/wp/v2/posts?per_page=1` is definitive, or
just check the page source for `wp-content`/`wp-json` if being fast about
it). This phase can run in parallel across regions — it's pure research,
no code, no shared state to conflict over.

**Phase 2 — test & implement, region by region, smallest first.** For each
outlet flagged as promising in its region file:
1. Confirm the WP REST API is actually live and unauthenticated:
   `curl -s "<base_url>/wp-json/wp/v2/posts?per_page=1"` should return JSON,
   not a 401/403/404 or an HTML challenge page.
2. Check `robots.txt` for a `Crawl-delay` that makes it impractical, or a
   disallow on `/wp-json/`. (Precedent: `elmagallanews` was ruled out this
   way — see `DISABLED_SOURCES` in `vault/app.py`.)
3. If viable: add a new scraper file under `vault/scrapers/<source_id>.py`,
   subclassing `WordPressScraper` (see any existing Magallanes source, e.g.
   `vault/scrapers/elmagallanico.py`, for the ~10-line pattern — just
   `name`, `base_url`, `min_delay`). **Check the `per_page` default is
   actually safe for that host before assuming 100 works** — confirmed
   live 2026-08-22 that a slow/cheap WP host can silently fail on
   `per_page=100` combined with `_embed` (see `ovejeronoticias.py` for the
   `per_page = 10` override pattern and the project memory entry explaining
   why). A quick manual timing test (like the curl tests done for
   ovejeronoticias) before wiring it in avoids repeating that whole
   debugging cycle.
4. Register it: `vault/app.py`'s `SOURCE_GROUPS` (add to a new or existing
   region group), `SOURCE_NAMES`, and give it an entry in `db.ARCHIVE_STARTS`
   (a reasonable guess at how far back the site's archive goes — doesn't
   need to be exact, `mode=update`'s 2-day-lookback logic self-corrects
   over time, but see the `biobiochile`/`cnnchile` lesson below).
5. Run a *small, bounded* first test — `mode=full` on a **narrow recent
   date range first** (e.g. last 30 days via `date_from`/`date_to`), not an
   immediate full historical backfill. Confirm real articles land with
   real body text before trusting the source enough to let it run
   unattended. Full historical backfill is a deliberate, separate,
   one-at-a-time step per source (see `nightly_archive.py`'s own docstring
   for why — this is an existing, hard-won project rule, not new).
6. If not viable (no API, paywalled, proprietary CMS): leave it documented
   in the region file with why, same pattern as `DISABLED_SOURCES` — don't
   just delete the finding, a "we checked, it's not viable, here's why" is
   valuable and saves someone re-discovering the same dead end.
7. Once a region's outlets are all triaged (even if only 1-2 turn out
   viable — that's a fine outcome, quality over forcing coverage), mark it
   done in `STATUS.md` and move to the next-smallest region.

**Do not let `nightly_enabled` default to true blindly for a source with a
huge/unknown archive start** — the `biobiochile`/`cnnchile` incident
(2026-08-22, see project memory) happened because `mode=update`'s
"2 days before max_date" logic has no upper bound, and a source that's
never been backfilled or was abandoned years ago will make the nightly
timer try to walk its entire history every single night, indefinitely,
silently. Give every new source a real first backfill before trusting it
to the nightly rotation.

## Reconciliation note (found 2026-08-22, mid-project)

`vault/scrapers/__init__.py` has its own `GROUPS`/`_SCRAPERS` registry that
is **not the same thing** `vault/app.py` actually uses to drive the running
app. `app.py` imports only `get_scraper()` from that module and maintains
its own hand-written `SOURCE_GROUPS`/`SOURCES`/`SOURCE_NAMES` — which is
the *actually authoritative* list for what's reachable via routes/UI.
`scrapers/__init__.py`'s `GROUPS` dict is a second, parallel bookkeeping
structure that's currently disconnected from the live app (a leftover from
an earlier, apparently-unfinished refactor attempt — before this campaign
started, it already had extra sources coded, like `ellanquihue`, that were
never wired into `app.py` and so were silently unreachable). **Register
every new source in `app.py`'s `SOURCE_GROUPS`/`SOURCES`/`SOURCE_NAMES` —
that's what actually matters for it to work** — and additionally keep
`scrapers/__init__.py`'s `GROUPS` in sync too, purely for consistency with
the existing convention, not because anything currently reads it. Don't
spend time trying to "fix" this dual-registry situation as part of this
campaign unless explicitly asked — it's a pre-existing quirk, noted here so
nobody wastes time confused by it or assumes a source is live just because
it's in `_SCRAPERS`.

**Also found from this**: code existing in `vault/scrapers/` does not mean
it's currently viable. `ellanquihue.py` looked fully done (a real scraper
class, seemingly ready), but live-testing during this campaign found its
target domain's REST API now 404s — the site likely changed domains or
disabled the API since that code was written. Always re-verify live before
trusting old code, the same way a phase-1 census "confirmed WordPress" verdict is re-verified in phase 2 before wiring anything in for real.

## Where the documentation surfaces in the app

The user explicitly wants this discoverable from the app itself, not just
sitting in this repo. **TODO (not yet built as of 2026-08-22): add a
route to `vault/app.py`** — something like `/expansion` — that reads
`STATUS.md` (or a small JSON summary next to it, whichever is easier to
keep in sync) and renders it, linked from `vault/templates/index.html`'s
header alongside the existing "Explorar" link. Keep it simple: a table of
region → status → outlet count → viable count is enough, doesn't need to
be fancy. Build this once there's real STATUS.md content worth showing —
no point building the viewer before there's anything to view.

## Code patterns to reuse (don't reinvent these)

- **WordPress scraper**: `vault/scrapers/wordpress.py` (`WordPressScraper`
  base class) + any existing Magallanes subclass as a template.
- **Non-WP custom scraper**: `vault/scrapers/radiopolar.py` is the one
  precedent (Next.js site, JSON API discovered by inspecting network
  requests) — higher effort, only worth it for an outlet that's clearly
  worth the investment (biggest regional player with no WP alternative).
- **Source registration**: `SOURCE_GROUPS`, `SOURCE_NAMES`,
  `DISABLED_SOURCES` (for documented non-viable ones), all in
  `vault/app.py` near the top. `db.ARCHIVE_STARTS` in `vault/db.py`.
- **Author field**: already wired into `WordPressScraper.run()` generically
  (via `_embed=author`) — any new WP source gets it for free, no extra
  work needed, unlike the Magallanes sources which needed a retrofit.
- **Rebuilding after a scraper/app.py change**: source isn't bind-mounted,
  the image has to be rebuilt: `cd /home/mnx/camplux && docker compose
  build vault && docker compose up -d vault` (a few seconds of Vault
  downtime, Quarry/Caddy untouched — safe, done many times this project).

## Resuming after a context reset / new agent

1. Read this file (you just did).
2. Read `STATUS.md` in this same directory for exactly where things stand.
3. Check `deploy/logs_ovejero_gapfill.log` and `.ovejero_gapfill_progress.json`
   — unrelated to this expansion but was running concurrently when this
   project started; don't confuse its log noise for expansion work.
4. Check project memory (`project_camplux.md`) for anything logged there
   too — significant milestones get written there as well as here.
5. Pick the smallest region marked "not started" or "in progress" in
   `STATUS.md` and continue.
