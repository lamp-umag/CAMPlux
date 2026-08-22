# Maule — media census

Researched: 2026-08-22

## Outlets found

| Outlet | URL | Type | WordPress? | Notes |
|---|---|---|---|---|
| Diario Talca | https://diariotalca.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. |
| El Maule Informa | https://elmauleinforma.cl | digital-native | yes (API live) | Confirmed live JSON. Self-described independent/pluralist outlet, Talca-based. |
| Radio Chilena del Maule | https://radiochilenadelmaule.cl | radio | yes (API live) | Confirmed live JSON. Operates 91.7/1090 in Talca and 92.1 in Molina, plus sister station Radio Familia. |
| Diario El Centro | https://diarioelcentro.cl | newspaper (digital) | yes (API live) | Bare domain redirects; confirmed live JSON. Covers Talca, Curicó, and the wider region. |
| Crónica Noticias | https://cronicanoticias.cl | digital-native | yes (API live) | Confirmed live JSON, active recent posts. Curicó province, strong social-media presence per search results. |
| Diario Linares | https://diariolinares.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. Part of a small self-described "Red de Diarios del Maule" chain (regional, not national). |
| Diario Cauquenes | https://diariocauquenes.cl | newspaper (digital) | yes (API live) | Confirmed live JSON. Same "Red de Diarios del Maule" chain as Diario Linares. |
| Linares en Línea | https://www.linaresenlinea.cl | digital-native | yes (API live) | Confirmed live JSON. |
| CauquenesNet | https://cauquenesnet.cl | digital-native | yes (API live) | Confirmed live JSON, active recent posts. Covers Cauquenes, Chanco, Pelluhue. |
| TV5 Linares | https://www.tv5.cl | digital-native/TV | yes (API live) | Bare domain redirects; confirmed live JSON after following. Covers Linares and the region. |
| Prensa Curicó | https://prensacurico.cl | newspaper (digital) | no | `/wp-json/...` returns 404, but the site itself is live (its `/portal/` path returns 200) — different URL structure/CMS, not WordPress at the standard path. Provincial digital paper. |
| El Amaule | https://www.elamaule.cl | digital-native | no | `/wp-json/...` returns 404 after following redirect. Covers Curicó and Talca; likely custom CMS — needs closer look. |
| TeleCauquenes | https://www.telecauquenes.cl | digital-native/TV | no | `/wp-json/...` returns 404 after following redirect. Covers Cauquenes, Chanco, Curanipe, Pelluhue. |
| Maule News | https://www.maulenews.com | digital-native | no | `/wp-json/...` returns 404 (bare and `www.`). Self-described independent regional portal. |
| Red Maule | https://www.redmaule.com | digital-native | no | `/wp-json/...` returns 404 (bare and `www.`). Talca-based "Diarios en Red" aggregator/portal, run by Merelec SPA — mixes regional/national/international content, so worth a closer editorial-scope check in phase 2 even though it's not WordPress. |

## Summary

Found 15 candidate outlets, well spread across Talca, Curicó, Linares, and Cauquenes provinces. 10 of the 15 are confirmed WordPress with a live, open REST API (Diario Talca, El Maule Informa, Radio Chilena del Maule, Diario El Centro, Crónica Noticias, Diario Linares, Diario Cauquenes, Linares en Línea, CauquenesNet, TV5 Linares) — a strong phase-2 haul, notably including a small in-region print chain ("Red de Diarios del Maule" — Linares + Cauquenes titles). The remaining 5 (Prensa Curicó, El Amaule, TeleCauquenes, Maule News, Red Maule) are not WordPress at the standard path and would need custom scraping or a closer look at their actual structure; none were unreachable/DNS-dead in this pass.

## Phase 2 — implemented 2026-08-22

Re-verified all 10 census "yes (API live)" outlets live before wiring
anything in.

**TV5 Linares turned out to be a false positive** — re-verification found a
Next.js frontend (`__NEXT_DATA__` in the HTML, dedicated Google-News
sitemaps, `x-powered-by: Next.js`-style stack), not WordPress; `/wp-json/`
doesn't exist at that path. Documented in `DISABLED_SOURCES`, no scraper
file — would need a custom sitemap scraper (like `radiopolar.py`) to be
worth revisiting, not justified for a single channel.

**9 outlets are live in production** (`vault/scrapers/`, registered under
`app.py`'s `maule` group): **Diario Talca, El Maule Informa, Radio Chilena
del Maule, Diario El Centro, Crónica Noticias, Diario Linares, Diario
Cauquenes, Linares en Línea, CauquenesNet**.

- **Diario Talca, Diario Linares, and Diario Cauquenes share an identical
  network launch post** (`la-voz-de-los-talquinos`, dated 2020-12-03,
  identical slug/timestamp on all three domains) — confirms the census's
  "Red de Diarios del Maule" chain finding, extended to include Diario
  Talca as a fourth network member not flagged as part of the chain in the
  census. Each domain otherwise has its own large, distinct archive (X-WP-
  Total 20421 / 7687 / 6821 respectively) with real city-specific recent
  content (O'Higgins-day parade coverage in Talca, beekeeper training in
  Yerbas Buenas/Linares, MINVU rain-alert coverage in Cauquenes) — a shared
  seed post from a common network setup, not mirrored/duplicate content.
  All three registered as separate sources.
- **CauquenesNet has a genuine digitized historical archive back to
  2000-03-12** — checked for continuity (real political-history posts
  about the 2000 municipal elections and the "Caravana de la Muerte"
  exhumations in Cauquenes, not a data-entry typo), same class as
  `diarioelmarino.cl`'s 1907 archive in O'Higgins. Used as the real
  `ARCHIVE_STARTS` date.
- **Radio Chilena del Maule is dormant-but-real** — only 31 posts total,
  newest from 2023-02-02, but confirmed real content (COVID-19 coverage,
  municipal news, bylined by Mauricio Gallegos), not a placeholder
  install. Got a one-time `mode=full` backfill (31/31 saved) instead of the
  nightly rotation.
- **Diario El Centro's bare domain 301-redirects to `www.`** — `base_url`
  set directly to `https://www.diarioelcentro.cl` to skip the extra hop.
- No `per_page` or UA overrides needed anywhere in this region — every
  timing test (`per_page=100` + full `_embed`/`_fields`) came back well
  under budget, from ~1.5s (Crónica Noticias, smallest archive) to ~7.3s
  (Diario Talca, largest).
- robots.txt across the "Red de Diarios del Maule" domains (Talca/Linares/
  Cauquenes) carries a Cloudflare-managed block naming specific AI-crawler
  user agents (GPTBot, ClaudeBot, Google-Extended, etc.) with `Disallow:
  /`, but `User-agent: *` is `Allow: /` — since camplux's scraper doesn't
  identify as any of those named bots, this doesn't block us per
  robots.txt's own per-user-agent matching rules, same treatment as every
  prior region's generic-UA check. Noted here since it's the first time
  this specific pattern (named-bot exclusion list) showed up in the
  campaign.
