"""
National sources with custom CMSs — not yet implemented.
"""
from .base import BaseScraper


class _DisabledScraper(BaseScraper):
    region  = "nacional"
    enabled = False

    def run(self, **kwargs):
        yield {"type": "log", "level": "error",
               "msg": f"{self.name} no está soportado: {self.note}"}


class MeganoticiasScraper(_DisabledScraper):
    name = "Meganoticias"; base_url = "https://www.meganoticias.cl"
    note = "CMS propietario Viasat, sin API pública"

class LaTerceraScraper(_DisabledScraper):
    name = "La Tercera"; base_url = "https://www.latercera.com"
    note = "CMS propio, detrás de paywall parcial"

class T13Scraper(_DisabledScraper):
    name = "T13"; base_url = "https://www.t13.cl"
    note = "CMS Canal 13, sin WP REST API"

class Horas24Scraper(_DisabledScraper):
    name = "24 Horas"; base_url = "https://www.24horas.cl"
    note = "CMS TVN propietario"

class ChvNoticiasScraper(_DisabledScraper):
    name = "CHV Noticias"; base_url = "https://www.chvnoticias.cl"
    note = "CMS Chilevisión, sin API"

class EmolScraper(_DisabledScraper):
    name = "Emol"; base_url = "https://www.emol.com"
    note = "CMS El Mercurio propietario"

class CooperativaScraper(_DisabledScraper):
    name = "Radio Cooperativa"; base_url = "https://www.cooperativa.cl"
    note = "CMS propio, sin WP REST API"

class DiarioFinancieroScraper(_DisabledScraper):
    name = "Diario Financiero"; base_url = "https://www.df.cl"
    note = "Detrás de suscripción, sin API pública"

class PautaScraper(_DisabledScraper):
    name = "Pauta"; base_url = "https://www.pauta.cl"
    note = "Infraestructura La Tercera, sin WP API independiente"

class ElMercurioScraper(_DisabledScraper):
    name = "El Mercurio"; base_url = "https://www.elmercurio.com"
    note = "CMS propietario Grupo El Mercurio, paywall"

class LunScraper(_DisabledScraper):
    name = "Las Últimas Noticias"; base_url = "https://www.lun.com"
    note = "Grupo El Mercurio, CMS propietario"

class LaSegundaScraper(_DisabledScraper):
    name = "La Segunda"; base_url = "https://www.lasegunda.com"
    note = "Grupo El Mercurio, CMS propietario"

class ElLiberoScraper(_DisabledScraper):
    name = "El Líbero"; base_url = "https://ellibero.cl"
    note = "CMS propio, sin WP REST API verificada"
