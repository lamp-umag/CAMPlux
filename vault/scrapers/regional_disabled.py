"""
Regional sources (non-Magallanes) not yet verified as scrapeable.
"""
from .base import BaseScraper


class _DisabledRegionalScraper(BaseScraper):
    region  = "regional"
    enabled = False

    def run(self, **kwargs):
        yield {"type": "log", "level": "error",
               "msg": f"{self.name} no está soportado: {self.note}"}


class ElSurScraper(_DisabledRegionalScraper):
    name = "El Sur"; base_url = "https://www.elsur.cl"
    note = "CMS propio, sin WP REST API confirmada"

class AustralTemucoScraper(_DisabledRegionalScraper):
    name = "El Austral de Temuco"; base_url = "https://www.australtemuco.cl"
    note = "Grupo El Mercurio, CMS propietario"

class MercurioValpoScraper(_DisabledRegionalScraper):
    name = "El Mercurio de Valparaíso"; base_url = "https://www.mercuriovalpo.cl"
    note = "Grupo El Mercurio, CMS propietario"
