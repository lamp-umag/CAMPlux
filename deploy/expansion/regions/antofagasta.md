# Antofagasta — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| El Diario de Antofagasta | https://www.diarioantofagasta.cl | digital-native | yes (API live) | The region's most-read digital outlet; ~14 years old, covers Antofagasta, Calama, San Pedro de Atacama, Tocopilla, Mejillones, Taltal. Clear top pick for phase 2. |
| Diario Regionalista Antofagasta | https://regionalista.cl | digital-native | yes (API live) | Independent, covers Antofagasta, Calama, Tocopilla, Taltal, San Pedro de Atacama, Ollagüe, Sierra Gorda, Mejillones, María Elena. Investigative-leaning. |
| El Nortero | https://www.elnortero.cl | digital-native | no / unknown | Covers Antofagasta and Calama. Root loads (200), zero WP markers, wp-json 404 — likely a non-WP build. |
| El Mercurio de Antofagasta | https://www.mercurioantofagasta.cl | newspaper (digital) | possible WP, API blocked | Regional edition of the El Mercurio chain. ~14 wp-content-style references on homepage but `/wp-json/` 404s — ambiguous, worth a closer look rather than a firm "no". |
| El Mercurio de Calama | https://www.mercuriocalama.cl | newspaper (digital) | possible WP, API blocked | Same chain/CMS pattern as El Mercurio de Antofagasta; same caveat. |
| La Estrella de Antofagasta (formerly La Estrella del Norte) | https://www.soyantofagasta.cl | newspaper (digital) | unknown / connection error | Historic paper (founded 1966), part of the El Mercurio "Soy" chain. Site would not respond to curl at all, even with a browser user-agent — inconclusive, needs a closer look (possibly aggressive bot protection). |
| Radio Nuevo Mundo | https://radionuevomundo.cl | radio (news site) | yes (API live) | 104.7 FM Antofagasta; multi-city chain station with a national/regional news mix. |
| Nuevo Norte FM | https://nuevonortefm.cl | radio (news site) | yes (API live) | |

## Summary

8 outlets found — thinner than the other three regions census'd this round, consistent with Antofagasta's press landscape being dominated by a small number of players (mining-region cities, historically only 2 print dailies ever circulated). 4 of 8 look WordPress-viable (2 confirmed API-live, El Diario de Antofagasta and Regionalista — both digital-native and clearly the strongest candidates; 2 radio stations also API-live). The two El Mercurio regional-chain papers and the Estrella/Soy chain paper are all ambiguous or unreachable and will need real browser-level inspection in phase 2 rather than a plain curl. El Nortero looks like a non-WP custom site.

## Phase 2 — implemented 2026-08-22

Re-verified all 4 census "yes (API live)" outlets live before wiring anything
in.

**Nuevo Norte FM (nuevonortefm.cl) was ruled out** — a new kind of census
false positive: the WP REST API genuinely works and returns real JSON, but
every one of its 8 indexed posts is stock demo content from the "Gavias"
WordPress theme — "¡Hola, mundo!" (the default WP placeholder) plus filler
posts like "Live Stream From Awwwards Showcasing Trends" and "A day in the
life of entrepreneur & ceo", one of them with a `guid` literally pointing at
`gaviaspreview.com`. The site was set up and immediately abandoned before
any real content went in — same family as `diariodeaysen`'s "Hello World"
finding, just with a fuller (but entirely fake) placeholder archive instead
of a single post. Documented in `DISABLED_SOURCES` (`app.py`, region
`antofagasta`), no scraper file.

**3 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `antofagasta` group): **El Diario de Antofagasta, Diario
Regionalista Antofagasta, Radio Nuevo Mundo**. None had a disqualifying
`robots.txt` restriction (no Crawl-delay on any of the three; El Diario de
Antofagasta disallows `/cgi-bin/`, `/wp-admin/`, `/archives/`,
`*?replytocom` but not `/wp-json/`). `per_page=100` + full
`_embed`/`_fields` timed 2.5-4.5s for all three — no `per_page` override
needed, no UA blocking encountered.

Verified with a real `mode=range` test (2026-08-01 to 2026-08-22, all
`seen == saved`): El Diario de Antofagasta 226, Diario Regionalista
Antofagasta 76, Radio Nuevo Mundo 209 real recent articles saved cleanly.
Real body text (0.3-7.8KB per article) confirmed via spot-check; El Diario
de Antofagasta and Radio Nuevo Mundo both carry real author bylines out of
the box.

`ARCHIVE_STARTS` set to each site's real oldest-indexed post (confirmed via
`?orderby=date&order=asc`, not guessed): El Diario de Antofagasta
2011-02-07 (the deepest archive found in this region so far, 33,174 total
posts per `X-WP-Total`), Diario Regionalista Antofagasta 2018-03-05, Radio
Nuevo Mundo 2017-01-03. Left `nightly_enabled` at its default for all
three — no dormancy, all had a fresh post within the last 2 days.

The 4 census "possible WP, blocked"/"unknown"/"no" outlets (El Nortero, El
Mercurio de Antofagasta, El Mercurio de Calama, La Estrella de Antofagasta)
were left untouched — out of this task's scope (only "yes (API live)"
outlets were re-verified/wired in this pass).

Antofagasta is DONE — both phases complete for the "yes (API live)" set
from the census.
