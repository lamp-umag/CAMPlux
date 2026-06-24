# ── Magallanes ────────────────────────────────────────────────────────────────
from .laprensaaustral import LaPrensaAustralScraper
from .elpinguino      import ElPinguinoScraper
from .radiopolar      import RadioPolarScraper
from .elmagallanico   import ElMagallanicoScraper
from .ovejeronoticias import OvejeroNoticiasScraper
from .sosmagallanes   import SosMagallanesScraper
from .radiomagallanes import RadioMagallanesScraper
from .pepenoticias    import PepeNoticiasScraper
from .dialogosur      import DialogoSurScraper
from .itvpatagonia    import ItvPatagoniaScraper
from .zonazero        import ZonaZeroScraper

# ── Nacional (enabled) ────────────────────────────────────────────────────────
from .biobiochile   import BioBioChileScraper
from .elmostrador   import ElMostradorScraper
from .ciperchile    import CiperChileScraper
from .theclinic     import TheClinicScraper
from .eldinamo      import ElDinamoScraper
from .exante        import ExAnteScraper
from .elciudadano   import ElCiudadanoScraper
from .interferencia  import InterferenciaScraper
from .cnnchile       import CnnChileScraper
from .eldesconcierto import ElDesconciertoScraper

# ── Nacional (disabled) ───────────────────────────────────────────────────────
from .national_disabled import (
    MeganoticiasScraper, LaTerceraScraper, T13Scraper, Horas24Scraper,
    ChvNoticiasScraper, EmolScraper, CooperativaScraper,
    DiarioFinancieroScraper, PautaScraper,
    ElMercurioScraper, LunScraper, LaSegundaScraper, ElLiberoScraper,
)

# ── Regional (enabled) ────────────────────────────────────────────────────────
from .ladiscusion  import LaDiscusionScraper
from .ellanquihue  import ElLanquihueScraper

# ── Regional (disabled) ───────────────────────────────────────────────────────
from .regional_disabled import ElSurScraper, AustralTemucoScraper, MercurioValpoScraper

# ── Internacional ─────────────────────────────────────────────────────────────
from .techcrunch         import TechCrunchScraper
from .variety            import VarietyScraper
from .rollingstone       import RollingStoneScraper
from .hollywoodreporter  import HollywoodReporterScraper
from .technologyreview   import TechnologyReviewScraper
from .clarin             import ClarinScraper
from .theguardian        import TheGuardianScraper

# ── Registry ──────────────────────────────────────────────────────────────────
_SCRAPERS = {
    # Magallanes
    "laprensaaustral": LaPrensaAustralScraper(),
    "elpinguino":      ElPinguinoScraper(),
    "radiopolar":      RadioPolarScraper(),
    "elmagallanico":   ElMagallanicoScraper(),
    "ovejeronoticias": OvejeroNoticiasScraper(),
    "sosmagallanes":   SosMagallanesScraper(),
    "radiomagallanes": RadioMagallanesScraper(),
    "pepenoticias":    PepeNoticiasScraper(),
    "dialogosur":      DialogoSurScraper(),
    "itvpatagonia":    ItvPatagoniaScraper(),
    "zonazero":        ZonaZeroScraper(),
    # Nacional — enabled
    "biobiochile":   BioBioChileScraper(),
    "elmostrador":   ElMostradorScraper(),
    "ciperchile":    CiperChileScraper(),
    "theclinic":     TheClinicScraper(),
    "eldinamo":      ElDinamoScraper(),
    "exante":        ExAnteScraper(),
    "elciudadano":   ElCiudadanoScraper(),
    "interferencia":  InterferenciaScraper(),
    "cnnchile":       CnnChileScraper(),
    "eldesconcierto": ElDesconciertoScraper(),
    # Nacional — disabled
    "meganoticias": MeganoticiasScraper(),
    "latercera":    LaTerceraScraper(),
    "t13":          T13Scraper(),
    "24horas":      Horas24Scraper(),
    "chvnoticias":  ChvNoticiasScraper(),
    "emol":         EmolScraper(),
    "cooperativa":  CooperativaScraper(),
    "df":           DiarioFinancieroScraper(),
    "pauta":        PautaScraper(),
    "elmercurio":   ElMercurioScraper(),
    "lun":          LunScraper(),
    "lasegunda":    LaSegundaScraper(),
    "ellibero":     ElLiberoScraper(),
    # Regional — enabled
    "ladiscusion": LaDiscusionScraper(),
    "ellanquihue": ElLanquihueScraper(),
    # Regional — disabled
    "elsur":         ElSurScraper(),
    "australtemuco": AustralTemucoScraper(),
    "mercuriovalpo": MercurioValpoScraper(),
    # Internacional
    "techcrunch":        TechCrunchScraper(),
    "variety":           VarietyScraper(),
    "rollingstone":      RollingStoneScraper(),
    "hollywoodreporter": HollywoodReporterScraper(),
    "technologyreview":  TechnologyReviewScraper(),
    "clarin":            ClarinScraper(),
    "theguardian":       TheGuardianScraper(),
}

# ── Source groups (for UI group tabs) ─────────────────────────────────────────
GROUPS = {
    "magallanes": {
        "label": "Magallanes",
        "sources": [
            "laprensaaustral", "elpinguino", "radiopolar", "elmagallanico",
            "ovejeronoticias", "sosmagallanes", "radiomagallanes", "pepenoticias",
            "dialogosur", "itvpatagonia", "zonazero",
        ],
    },
    "nacional": {
        "label": "Nacional",
        "sources": [
            "biobiochile", "elmostrador", "ciperchile", "theclinic",
            "eldinamo", "exante", "elciudadano", "interferencia",
            "cnnchile", "eldesconcierto",
            "meganoticias", "latercera", "t13", "24horas",
            "chvnoticias", "emol", "elmercurio", "lun", "lasegunda",
            "ellibero", "cooperativa", "df", "pauta",
        ],
    },
    "regional": {
        "label": "Otras regiones",
        "sources": [
            "ladiscusion", "ellanquihue",
            "elsur", "australtemuco", "mercuriovalpo",
        ],
    },
    "internacional": {
        "label": "Internacional",
        "sources": [
            "techcrunch", "variety", "rollingstone",
            "hollywoodreporter", "technologyreview",
            "clarin", "theguardian",
        ],
    },
}


def get_scraper(source_id):
    return _SCRAPERS.get(source_id)


def source_meta():
    """Return source_id → metadata dict for the UI."""
    result = {}
    for sid, scraper in _SCRAPERS.items():
        result[sid] = {
            "name":    scraper.name,
            "url":     scraper.base_url.replace("https://www.", "").replace("https://", ""),
            "region":  scraper.region,
            "enabled": scraper.enabled,
            "note":    scraper.note,
        }
    return result


__all__ = ["get_scraper", "_SCRAPERS", "GROUPS", "source_meta"]
