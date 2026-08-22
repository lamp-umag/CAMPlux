# Valparaíso — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| El Mercurio de Valparaíso | https://www.mercuriovalpo.cl | newspaper | no (404, custom) | Oldest continuously-published Spanish-language newspaper in the world (founded 1827). Regional flagship; part of the El Mercurio/SVS group but a distinct regional title, not the Santiago El Mercurio/Emol (which are out of scope). |
| La Estrella de Valparaíso | https://www.estrellavalpo.cl | newspaper | no (404, custom) | Tabloid-style regional daily since 1921, same ownership group (El Mercurio de Valparaíso S.A.P.) as the above. |
| El Líder de San Antonio | https://www.lidersanantonio.cl | newspaper | no (404, custom) | San Antonio local paper since 1995, also part of the El Mercurio de Valparaíso regional chain. |
| El Observador | https://www.observador.cl | digital-native / newspaper | **yes (API live)** | Covers Quillota, Petorca, San Felipe, Marga Marga and Valparaíso provinces. Good scraper candidate. |
| G5 Noticias | https://g5noticias.cl | digital-native | **yes (API live)** | Multiplatform news from Valparaíso region professionals. Good scraper candidate. |
| El Martutino | https://www.elmartutino.cl | digital-native | no (404, custom) | Valparaíso / Viña del Mar news. |
| Diario La Quinta | https://diariolaquinta.cl | digital-native | **yes (API live)** | Valparaíso — noticias, opinión, cultura, eventos. Good scraper candidate. |
| Epicentro Chile | https://www.epicentrochile.com | digital-native | **yes (API live)** | Based in Valparaíso/Viña, but framing leans broader ("Chile y el mundo") — borderline between regional and general-interest; worth a closer editorial look in Phase 2. |
| Red Valparaíso | https://www.redvalparaiso.com | digital-native | no (404, custom) | Covers Quillota, San Antonio, San Felipe, Marga Marga. |
| Red Noticias V Región | https://www.rednoticiasvregion.cl | digital-native | no — looks like a Next.js/React app, not WordPress | Regional news, modern JS-driven front end. |
| Los Andes Online | https://www.losandesonline.cl | digital-native | no (404, custom) | First digital outlet of the Aconcagua valley (online since 2001), based in Los Andes. |
| Diario El Trabajo | https://www.eltrabajo.cl | newspaper | no (404, custom) | San Felipe — oldest media outlet in the Aconcagua valley, founded 1929. |
| El Aconcagua | https://www.elaconcagua.cl | digital-native | **yes (API live)** | San Felipe / Aconcagua valley. Good scraper candidate. |
| Radio Portales de Valparaíso | https://portalesfm.cl | radio | **yes (API live)** | News-focused Valparaíso radio since 1960, 840 AM / 89.5 FM. Good scraper candidate. |
| Proa Regional (El Proa) | https://elproa.cl | digital-native | **yes (API live)** | San Antonio. Good scraper candidate. |
| Soy Quillota / Soy Valparaíso | https://www.soychile.cl/quillota, https://www.soychile.cl/valparaiso | digital-native | n/a — subsections of the national SoyChile network, not standalone sites | Included for completeness; not distinct scrape targets. |

A few names turned up in directory listings without a confirmable live
domain and were left out of the table rather than guessed at: **El
Informador** (Los Andes), **Más Noticia** (Quillota), **La Región Hoy**,
and **Diario El Marino** (San Antonio). Worth a closer manual look if this
region's Phase 2 needs more candidates.

## Summary

16 confirmed candidate outlets found (plus a handful of unconfirmed names
noted above). Seven look WordPress-viable at a glance with a live, open
REST API: **El Observador, G5 Noticias, Diario La Quinta, Epicentro Chile,
El Aconcagua, Radio Portales de Valparaíso, Proa Regional**. As in Biobío,
the oldest/biggest legacy papers (El Mercurio de Valparaíso, La Estrella de
Valparaíso, El Líder de San Antonio, Los Andes Online, Diario El Trabajo)
all run custom CMSes with no exposed WP API. Coverage spans the full
region — Valparaíso/Viña, the Aconcagua valley (Los Andes, San Felipe),
Quillota/Marga Marga, and San Antonio province — with no obvious gap
except possibly Casablanca/Quintero/Puchuncaví, which mostly showed up
being covered by Diario La Quinta rather than having dedicated outlets of
their own.

## Phase 2 — implemented 2026-08-22

Re-verified all 7 census "yes (API live)" outlets live before wiring
anything in. Also cross-checked `mercuriovalpo` against this region's
finding (El Mercurio de Valparaíso, mercuriovalpo.cl, 404/custom CMS) —
already correctly disabled in `DISABLED_SOURCES`, only needed its `region`
field updated from the generic `"regional"` to `"valparaiso"` to match the
current per-region convention (no behavior change, purely a bookkeeping
fix).

**Radio Portales de Valparaíso confirmed not viable** — the WP REST API is
genuinely live (X-WP-Total 78), but every indexed post is a song-play log
entry ("El Deluki – Solito Los 2", "Casandra Paz – La Vida me Trajo Hasta
Aquí"), all under a `scroll` category; the site's real `actualidad`
(news) category exists but has 0 posts. A real, active WordPress install,
but its `posts` endpoint carries a music-rotation log, not editorial
content — no custom post type has the news either. Moved to
`DISABLED_SOURCES`, no scraper file.

**6 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `valparaiso` group): **El Observador, G5 Noticias, Diario La
Quinta, Epicentro Chile, El Aconcagua, El Proa**.

- **G5 Noticias has this region's (and one of the whole campaign's)
  biggest archives** — X-WP-Total 218838, oldest post 2020-01-08 —
  confirmed genuine on inspection (real local news: fires, ministers,
  municipal coverage), not a duplicate/multisite artifact. A full
  historical backfill would take a long time and was deliberately not run
  as part of this initial wiring-in, per `nightly_archive.py`'s own
  one-source-at-a-time backfill rule.
- **El Aconcagua**'s bare domain 301-redirects to `www.` — `base_url` set
  directly to `https://www.elaconcagua.cl`. Its robots.txt has
  `Crawl-delay: 10` — `min_delay = 10.0`, same treatment as Ovalle Hoy /
  HDN Digital precedents.
- **Epicentro Chile** stays borderline on editorial scope per the census
  note (broader "Chile y el mundo" framing) but is Valparaíso/Viña-
  headquartered and was kept in this region, same call as other
  borderline regional/national outlets elsewhere in this campaign.
- **Diario La Quinta**'s archive includes a meaningful share of court
  legal-notice classifieds (divorce/inheritance filings) alongside news —
  real content either way, not a data quality issue, just a mixed-content
  regional outlet.
- No `per_page` overrides needed anywhere in this region — every timing
  test (`per_page=100` + full `_embed`/`_fields`) came back under 15s,
  well within the 30s budget (El Aconcagua's own 14.2s absorbed by its
  Crawl-delay-driven `min_delay=10` regardless).
