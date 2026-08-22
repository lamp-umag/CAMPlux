"""
Portal Metropolitano — portalmetropolitano.cl
Broader RM/zona-central framing, flagged borderline general-interest by
the census. Editorial sample checked live 2026-08-22 (15 most recent
posts): consistently comuna/RM-local in practice -- Maipú youth programs,
Las Condes reinsertion program, Barrio Italia events, GAM art, Persa
Víctor Manuel, Punto Empleo -- genuinely metropolitan/community coverage,
not national politics or business. Kept in, unlike Duplos (see
DISABLED_SOURCES / metropolitana.md for the contrast and reasoning).
robots.txt: no crawl-delay/disallow on wp-json (a `Disallow: /*blackhole`
trap path is unrelated to wp-json). WP REST API confirmed live
2026-08-22: oldest indexed post 2022-09-05, newest same-day as check,
X-WP-Total 12309. per_page=100 + full _embed/_fields timed ~4.6s -- no
per_page override needed.
"""
from .wordpress import WordPressScraper


class PortalMetropolitanoScraper(WordPressScraper):
    name = "Portal Metropolitano"
    base_url = "https://portalmetropolitano.cl"
    region = "metropolitana"
    min_delay = 1.0
