import concurrent.futures as cf
import json
import datetime
import logging
import os
import re
import uuid
from logging.handlers import RotatingFileHandler
from flask import Flask, Response, jsonify, render_template, request
from flask import stream_with_context, send_from_directory, abort
from waitress import serve

import db
import scheduler_db
from scrapers import get_scraper

scheduler_db.init_db()

# ── logging setup ─────────────────────────────────────────────────────────────
_LOG_DIR = os.path.join(os.path.dirname(__file__), "data", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

_log_file = os.path.join(_LOG_DIR, "yene.log")
_file_handler = RotatingFileHandler(_log_file, maxBytes=5_000_000, backupCount=5,
                                     encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
_file_handler.setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), _file_handler],
)

app = Flask(__name__)

SOURCE_GROUPS = {
    "magallanes": {
        "label": "Magallanes",
        "sources": [
            "elpinguino", "dialogosur", "ovejeronoticias", "elmagallanico",
            "laprensaaustral", "pepenoticias", "zonazero", "itvpatagonia",
            "sosmagallanes", "radiomagallanes", "radiopolar",
        ],
    },
    "nacional": {
        "label": "Nacional",
        "sources": [
            "biobiochile", "elmostrador", "ciperchile", "theclinic",
            "elciudadano", "cnnchile",
        ],
    },
    "regional": {
        "label": "Otras regiones",
        "sources": ["ladiscusion"],
    },
    # ── National expansion, region by region, smallest population first ──────
    # (Censo 2024 order) -- see deploy/expansion/PLAN.md for the whole
    # campaign plan and deploy/expansion/STATUS.md for live progress.
    "aysen": {
        "label": "Aysén",
        "sources": [
            "diarioaysen", "canalsurpatagonia",
            "radiosantamaria", "rln",
        ],
    },
    "arica_parinacota": {
        "label": "Arica y Parinacota",
        "sources": [
            "aricahoy", "aricaldia", "elmorrodearica", "cappissimamultimedial",
        ],
    },
    "atacama": {
        "label": "Atacama",
        "sources": [
            "atacamanoticias", "chanarcillo", "tierramarillano",
            "hvaradio", "atacamaenlinea", "madero",
        ],
    },
    "tarapaca": {
        "label": "Tarapacá",
        "sources": [
            "diariolongino", "iquiquetv", "iquiquealdia",
            "radiopaulina", "rtccormudesi",
        ],
    },
    "los_rios": {
        "label": "Los Ríos",
        "sources": [
            "radioaustralvaldivia", "losriosaldia", "periodicolosrios",
            "noticiaslosrios", "rioenlinea", "diarioelranco",
        ],
    },
    "nuble": {
        "label": "Ñuble",
        "sources": [
            "nubleonline", "nubleactual", "lafontana", "quirihuenoticias",
            "radiocontacto", "radionuble",
        ],
    },
    "antofagasta": {
        "label": "Antofagasta",
        "sources": [
            "diarioantofagasta", "regionalista", "radionuevomundo",
        ],
    },
    "coquimbo": {
        "label": "Coquimbo",
        "sources": [
            "ovallehoy", "laserenaonline", "elcoquimbano", "elillapelino",
            "diariochoapa", "radioriquelme",
        ],
    },
    "los_lagos": {
        "label": "Los Lagos",
        "sources": [
            "diarioloslagos", "chiloenews", "laopiniondechiloe",
            "diariopuertovaras", "radiofrutillarfm",
        ],
    },
    "ohiggins": {
        "label": "O'Higgins",
        "sources": [
            "elrancaguino", "diarioelpulso", "radiomachali", "diariorancagua",
            "hdn", "tribunacolchagua", "diarioelmarino", "pichilemutv",
            "radiosantacruz",
        ],
    },
    "araucania": {
        "label": "Araucanía",
        "sources": [
            "araucanianoticias", "elperiodico", "malleconoticias",
            "angolnoticiasnew", "lasnoticiasdemalleco", "elespejodemalleco",
            "malleco7", "villarricaldia",
        ],
    },
    "maule": {
        "label": "Maule",
        "sources": [
            "diariotalca", "elmauleinforma", "radiochilenadelmaule",
            "diarioelcentro", "cronicanoticias", "diariolinares",
            "diariocauquenes", "linaresenlinea", "cauquenesnet",
        ],
    },
    "biobio": {
        "label": "Biobío",
        "sources": [
            "bionoticias", "elcontraste", "diarioprovincial", "araucovision",
        ],
    },
    "valparaiso": {
        "label": "Valparaíso",
        "sources": [
            "observador", "g5noticias", "diariolaquinta", "epicentrochile",
            "elaconcagua", "elproa",
        ],
    },
    "metropolitana": {
        "label": "Región Metropolitana",
        "sources": [
            "elcomunicador", "diarioellabrador", "portaldemelipilla",
            "puentealtoaldia", "puentealtonline", "portalpuentealto",
            "redhoy", "lavozdemaipu", "labatalla", "noticiasdelsol",
            "delh", "portalmetropolitano",
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

# All archiveable (enabled) sources ordered by group
SOURCES = (
    SOURCE_GROUPS["magallanes"]["sources"]
    + SOURCE_GROUPS["nacional"]["sources"]
    + SOURCE_GROUPS["regional"]["sources"]
    + SOURCE_GROUPS["aysen"]["sources"]
    + SOURCE_GROUPS["arica_parinacota"]["sources"]
    + SOURCE_GROUPS["atacama"]["sources"]
    + SOURCE_GROUPS["tarapaca"]["sources"]
    + SOURCE_GROUPS["los_rios"]["sources"]
    + SOURCE_GROUPS["nuble"]["sources"]
    + SOURCE_GROUPS["antofagasta"]["sources"]
    + SOURCE_GROUPS["coquimbo"]["sources"]
    + SOURCE_GROUPS["los_lagos"]["sources"]
    + SOURCE_GROUPS["ohiggins"]["sources"]
    + SOURCE_GROUPS["araucania"]["sources"]
    + SOURCE_GROUPS["maule"]["sources"]
    + SOURCE_GROUPS["biobio"]["sources"]
    + SOURCE_GROUPS["valparaiso"]["sources"]
    + SOURCE_GROUPS["metropolitana"]["sources"]
)

# Explorer originally scoped to Magallanes-only (2026-08-11 user request,
# back when Magallanes was the only developed region). Widened 2026-08-22
# as the national expansion campaign (see deploy/expansion/) landed real
# sources in 10+ other regions -- excluding them from search/CSV export
# would leave 45+ new sources invisible to the one UI meant to surface this
# content. Excludes only "internacional" (non-Chilean press, a different
# kind of corpus, mixing it into "search the whole archive" by default
# would be surprising) -- everything else (regional expansion + nacional +
# the legacy "regional" bucket) is in scope and grows automatically as
# more regions get added, no manual update needed per region.
EXPLORE_SOURCES = tuple(
    sid for group_key, info in SOURCE_GROUPS.items()
    if group_key != "internacional"
    for sid in info["sources"]
)

SOURCE_NAMES = {
    # Magallanes
    "elpinguino":      "El Pingüino",
    "dialogosur":      "Diálogo Sur",
    "ovejeronoticias": "Ovejero Noticias",
    "elmagallanico":   "El Magallánico",
    "laprensaaustral": "La Prensa Austral",
    "pepenoticias":    "Pepe Noticias",
    "zonazero":        "Zona Zero",
    "itvpatagonia":    "ITV Patagonia",
    "sosmagallanes":   "SOS Magallanes",
    "radiomagallanes": "Radio Magallanes",
    "radiopolar":      "Radio Polar",
    # Nacional
    "biobiochile":   "BioBioChile",
    "elmostrador":   "El Mostrador",
    "ciperchile":    "CIPER Chile",
    "theclinic":     "The Clinic",
    "elciudadano":   "El Ciudadano",
    "cnnchile":      "CNN Chile",
    # Regiones
    "ladiscusion":   "La Discusión",
    # Aysén (national expansion, see deploy/expansion/)
    "diarioaysen":       "Diario Aysén",
    "canalsurpatagonia": "Canal Sur Patagonia",
    "radiosantamaria":   "Radio Santa María",
    "rln":               "Radio Las Nieves",
    # Arica y Parinacota (national expansion)
    "aricahoy":              "Arica Hoy",
    "aricaldia":             "Arica al Día",
    "elmorrodearica":        "El Morro de Arica",
    "cappissimamultimedial": "Cappissima Multimedial",
    # Atacama (national expansion)
    "atacamanoticias":  "Atacama Noticias",
    "chanarcillo":      "Diario Chañarcillo",
    "tierramarillano":  "Tierramarillano",
    "hvaradio":         "HVA Radio",
    "atacamaenlinea":   "Atacama en Línea",
    "madero":           "Madero",
    # Tarapacá (national expansion)
    "diariolongino": "Diario El Longino",
    "iquiquetv":     "Iquique TV",
    "iquiquealdia":  "Iquique al Día",
    "radiopaulina":  "Radio Paulina",
    "rtccormudesi":  "RTC Televisión (CORMUDESI)",
    # Los Ríos (national expansion)
    "radioaustralvaldivia": "Radio Austral Valdivia",
    "losriosaldia":         "Los Ríos al Día",
    "periodicolosrios":     "Periódico Los Ríos",
    "noticiaslosrios":      "Noticias Los Ríos",
    "rioenlinea":           "Río en Línea",
    "diarioelranco":        "Diario El Ranco",
    # Ñuble (national expansion)
    "nubleonline":       "Ñuble Online",
    "nubleactual":       "Ñuble Actual",
    "lafontana":         "La Fontana",
    "quirihuenoticias":  "Quirihue Noticias",
    "radiocontacto":     "Radio Contacto 90.7 FM",
    "radionuble":        "Radio Ñuble",
    # Antofagasta (national expansion)
    "diarioantofagasta": "El Diario de Antofagasta",
    "regionalista":      "Diario Regionalista Antofagasta",
    "radionuevomundo":   "Radio Nuevo Mundo",
    # Coquimbo (national expansion)
    "ovallehoy":       "Ovalle Hoy",
    "laserenaonline":  "La Serena Online",
    "elcoquimbano":    "El Coquimbano",
    "elillapelino":    "El Illapelino",
    "diariochoapa":    "Diario Choapa",
    "radioriquelme":   "Radio Riquelme",
    # Los Lagos (national expansion)
    "diarioloslagos":    "Diario Digital Los Lagos",
    "chiloenews":        "ChiloeNews",
    "laopiniondechiloe": "La Opinión de Chiloé",
    "diariopuertovaras": "Diario Puerto Varas",
    "radiofrutillarfm":  "Radio Frutillar FM 96.7",
    # O'Higgins (national expansion)
    "elrancaguino":     "El Rancagüino",
    "diarioelpulso":    "Diario El Pulso",
    "radiomachali":     "Radio Machalí",
    "diariorancagua":   "Diario Rancagua",
    "hdn":              "HDN Digital",
    "tribunacolchagua": "Tribuna Colchagua",
    "diarioelmarino":   "El Marino",
    "pichilemutv":      "PichilemuTV",
    "radiosantacruz":   "Radio Santa Cruz",
    # Araucanía (national expansion)
    "araucanianoticias":   "Araucanía Noticias",
    "elperiodico":         "El Periódico",
    "malleconoticias":     "Malleco Noticias",
    "angolnoticiasnew":    "Angol Noticias",
    "lasnoticiasdemalleco":"Las Noticias de Malleco",
    "elespejodemalleco":   "El Espejo de Malleco",
    "malleco7":            "Malleco 7",
    "villarricaldia":      "Villarrica al Día",
    # Maule (national expansion)
    "diariotalca":          "Diario Talca",
    "elmauleinforma":       "El Maule Informa",
    "radiochilenadelmaule": "Radio Chilena del Maule",
    "diarioelcentro":       "Diario El Centro",
    "cronicanoticias":      "Crónica Noticias",
    "diariolinares":        "Diario Linares",
    "diariocauquenes":      "Diario Cauquenes",
    "linaresenlinea":       "Linares en Línea",
    "cauquenesnet":         "CauquenesNet",
    # Biobío (national expansion)
    "bionoticias":     "Bionoticias.cl",
    "elcontraste":     "El Contraste",
    "diarioprovincial":"Diario Provincial",
    "araucovision":    "Araucovisión",
    # Valparaíso (national expansion)
    "observador":     "El Observador",
    "g5noticias":     "G5 Noticias",
    "diariolaquinta": "Diario La Quinta",
    "epicentrochile": "Epicentro Chile",
    "elaconcagua":    "El Aconcagua",
    "elproa":         "El Proa",
    # Región Metropolitana (national expansion)
    "elcomunicador":     "El Comunicador",
    "diarioellabrador":  "Diario El Labrador",
    "portaldemelipilla": "Portal de Melipilla",
    "puentealtoaldia":   "Puente Alto Al Día",
    "puentealtonline":   "Puente Altonline",
    "portalpuentealto":  "Portal Puente Alto",
    "redhoy":            "RedHoy",
    "lavozdemaipu":      "La Voz de Maipú",
    "labatalla":         "La Batalla de Maipú",
    "noticiasdelsol":    "Noticias del Sol",
    "delh":              "El Amanecer de lo Herrera",
    "portalmetropolitano": "Portal Metropolitano",
    # Internacional
    "techcrunch":        "TechCrunch",
    "variety":           "Variety",
    "rollingstone":      "Rolling Stone",
    "hollywoodreporter": "The Hollywood Reporter",
    "technologyreview":  "MIT Technology Review",
    "clarin":            "Clarín",
    "theguardian":       "The Guardian",
}

# Disabled sources shown as read-only cards in the UI
DISABLED_SOURCES = {
    "elmagallanews": {
        "name":   "El Magallanews",
        "url":    "elmagallanews.cl",
        "region": "magallanes",
        "reason": "Crawl-delay 300 s en robots.txt. Sin API. No viable.",
    },
    "diariodeaysen": {
        "name":   "Diario de Aysén",
        "url":    "diariodeaysen.cl",
        "region": "aysen",
        "reason": "WP REST API responde, pero el sitio solo tiene el post "
                   "placeholder \"Hello World\" -- instalación nueva/en "
                   "construcción, sin contenido real. Revisar más adelante.",
    },
    "meganoticias": {
        "name":   "Meganoticias",
        "url":    "meganoticias.cl",
        "region": "nacional",
        "reason": "CMS propietario Viasat, sin API pública",
    },
    "latercera": {
        "name":   "La Tercera",
        "url":    "latercera.com",
        "region": "nacional",
        "reason": "CMS propio con paywall parcial",
    },
    "t13": {
        "name":   "T13",
        "url":    "t13.cl",
        "region": "nacional",
        "reason": "CMS Canal 13, sin WP REST API",
    },
    "24horas": {
        "name":   "24 Horas",
        "url":    "24horas.cl",
        "region": "nacional",
        "reason": "CMS TVN propietario",
    },
    "emol": {
        "name":   "Emol",
        "url":    "emol.com",
        "region": "nacional",
        "reason": "CMS El Mercurio propietario",
    },
    "elmercurio": {
        "name":   "El Mercurio",
        "url":    "elmercurio.com",
        "region": "nacional",
        "reason": "CMS propietario Grupo El Mercurio, paywall",
    },
    "lun": {
        "name":   "Las Últimas Noticias",
        "url":    "lun.com",
        "region": "nacional",
        "reason": "Grupo El Mercurio, CMS propietario",
    },
    "lasegunda": {
        "name":   "La Segunda",
        "url":    "lasegunda.com",
        "region": "nacional",
        "reason": "Grupo El Mercurio, CMS propietario",
    },
    "chvnoticias": {
        "name":   "CHV Noticias",
        "url":    "chvnoticias.cl",
        "region": "nacional",
        "reason": "CMS Chilevisión, sin API",
    },
    "df": {
        "name":   "Diario Financiero",
        "url":    "df.cl",
        "region": "nacional",
        "reason": "Detrás de suscripción, sin API pública",
    },
    "ellibero": {
        "name":   "El Líbero",
        "url":    "ellibero.cl",
        "region": "nacional",
        "reason": "CMS propio, sin WP REST API verificada",
    },
    "cooperativa": {
        "name":   "Radio Cooperativa",
        "url":    "cooperativa.cl",
        "region": "nacional",
        "reason": "CMS propio, sin WP REST API",
    },
    "elsur": {
        "name":   "El Sur",
        "url":    "elsur.cl",
        "region": "biobio",
        "reason": "CMS propio sin WP API confirmada",
    },
    "mercuriovalpo": {
        "name":   "El Mercurio de Valparaíso",
        "url":    "mercuriovalpo.cl",
        "region": "valparaiso",
        "reason": "Grupo El Mercurio, CMS propietario",
    },
    "australtemuco": {
        "name":   "El Austral de Temuco",
        "url":    "australtemuco.cl",
        "region": "regional",
        "reason": "Grupo El Mercurio, CMS propietario",
    },
    # Disabled pending sitemap-based scrapers (WP REST API missing/blocked)
    "eldinamo": {
        "name":   "El Dínamo",
        "url":    "eldinamo.cl",
        "region": "nacional",
        "reason": "Sin WP REST API. Pendiente scraper sitemap.",
    },
    "exante": {
        "name":   "Ex-Ante",
        "url":    "ex-ante.cl",
        "region": "nacional",
        "reason": "WAF bloquea acceso (HTTP 403). Pendiente otra estrategia.",
    },
    "interferencia": {
        "name":   "Interferencia",
        "url":    "interferencia.cl",
        "region": "nacional",
        "reason": "Sin WP REST API. Pendiente scraper sitemap.",
    },
    "eldesconcierto": {
        "name":   "El Desconcierto",
        "url":    "eldesconcierto.cl",
        "region": "nacional",
        "reason": "Sin WP REST API. Pendiente scraper sitemap.",
    },
    "ellanquihue": {
        "name":   "El Llanquihue",
        "url":    "ellanquihue.cl",
        "region": "regional",
        "reason": "Sin WP REST API. Pendiente scraper sitemap.",
    },
    # ── Los Ríos (national expansion) ─────────────────────────────────────────
    "noticiasriobueno": {
        "name":   "NoticiasRioBueno.com",
        "url":    "noticiasriobueno.com",
        "region": "los_rios",
        "reason": "WP REST API responde, pero robots.txt especifica "
                   "Crawl-delay: 3600 (1 hora) -- 12x peor que el precedente "
                   "elmagallanews (300s) ya descartado. No viable.",
    },
    # These 10 domains were flagged "yes (API live)" in the phase-1 census
    # (2026-08-22) but live re-verification during phase 2 (same day) found
    # /wp-json/wp/v2/posts returns plain HTML (200, text/html), not JSON,
    # and none of their homepages have any wp-content/wp-json markers --
    # they all share a different, non-WordPress proprietary CMS (robots.txt
    # has /base/printadv/, /estadset/, /base/clima.php -- not WP paths).
    # See regions/los-rios.md's phase 2 section for the full investigation.
    "diariodevaldivia": {
        "name":   "Diario de Valdivia",
        "url":    "diariodevaldivia.cl",
        "region": "los_rios",
        "reason": "Census marcó \"API live\" pero /wp-json no es WordPress "
                   "real (devuelve HTML, no JSON) -- CMS propietario "
                   "compartido con la red Diario Futrono. Ver los-rios.md.",
    },
    "diariofutrono": {
        "name":   "Diario Futrono",
        "url":    "diariofutrono.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diariodepanguipulli": {
        "name":   "Diario de Panguipulli",
        "url":    "diariodepanguipulli.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diarioriobueno": {
        "name":   "Diario Río Bueno",
        "url":    "diarioriobueno.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diariolaunion": {
        "name":   "Diario La Unión",
        "url":    "diariolaunion.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diariopaillaco": {
        "name":   "Diario Paillaco",
        "url":    "diariopaillaco.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diariocorral": {
        "name":   "Diario Corral",
        "url":    "diariocorral.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diariolagoranco": {
        "name":   "Diario Lago Ranco",
        "url":    "diariolagoranco.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diariolaguino": {
        "name":   "Diario Laguino",
        "url":    "diariolaguino.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    "diariomafil": {
        "name":   "Diario Máfil",
        "url":    "diariomafil.cl",
        "region": "los_rios",
        "reason": "No es WordPress real pese al hallazgo del censo -- ver "
                   "los-rios.md.",
    },
    # ── Ñuble (national expansion) ────────────────────────────────────────────
    "orbitanoticias": {
        "name":   "Órbita Noticias",
        "url":    "orbitanoticias.cl",
        "region": "nuble",
        "reason": "Censo marcó \"API live\" pero re-verificación en vivo "
                   "(2026-08-22) encontró que el sitio entero -- home y "
                   "wp-json por igual -- responde HTTP 200 con cuerpo "
                   "completamente vacío (content-length: 0), sin importar el "
                   "User-Agent. No es un bloqueo de API, es el servidor "
                   "entero devolviendo nada. No viable.",
    },
    # ── Antofagasta (national expansion) ──────────────────────────────────────
    "nuevonortefm": {
        "name":   "Nuevo Norte FM",
        "url":    "nuevonortefm.cl",
        "region": "antofagasta",
        "reason": "Censo marcó \"API live\" y la API en efecto responde, "
                   "pero re-verificación en vivo (2026-08-22) encontró que "
                   "todo el contenido indexado (8 posts) es texto de "
                   "demostración de un tema WordPress (Gavias) -- \"¡Hola, "
                   "mundo!\" más posts de relleno sobre \"Awwwards\" y "
                   "\"entrepreneur & ceo\", uno con guid apuntando a "
                   "gaviaspreview.com. Nunca se publicó contenido real. No "
                   "viable.",
    },
    # ── Coquimbo (national expansion) ─────────────────────────────────────────
    "miradiols": {
        "name":   "Mi Radio LS",
        "url":    "miradiols.cl",
        "region": "coquimbo",
        "reason": "Censo marcó \"API live\" pero robots.txt tiene "
                   "explícitamente \"Disallow: /wp-json/\" para User-agent: "
                   "* (bloque Yoast) -- el propio sitio prohíbe el acceso a "
                   "la ruta que necesitamos, pese a que la API responde si "
                   "se ignora robots.txt. No viable.",
    },
    # ── Los Lagos (national expansion) ────────────────────────────────────────
    "radiosago": {
        "name":   "Radio Sago",
        "url":    "radiosago.cl",
        "region": "los_lagos",
        "reason": "WP REST API responde HTTP 401 \"rest_login_required\" -- "
                   "bloqueada para usuarios no autenticados. No viable.",
    },
    "diariodeosorno": {
        "name":   "Diario de Osorno",
        "url":    "diariodeosorno.cl",
        "region": "los_lagos",
        "reason": "Censo marcó \"API live\" pero re-verificación en vivo "
                   "(2026-08-22) encontró que /wp-json/ devuelve el HTML de "
                   "la portada (200, text/html), no JSON -- no es "
                   "WordPress, es el mismo CMS propietario \"Grupo "
                   "DiarioSur\" que El Llanquihue (ya deshabilitado arriba, "
                   "región \"regional\"). No viable.",
    },
    # diariolaguino.cl (censused here as "Diario Laguino") is NOT a Los
    # Lagos region outlet -- it's the same domain already investigated and
    # disabled under the "los_rios" key above ("Los Lagos" comuna in Los
    # Ríos region, near Valdivia, not this region). Census
    # cross-contamination from the shared name, not re-added here. See
    # regions/los-lagos.md.
    # ── O'Higgins (national expansion) ────────────────────────────────────────
    "eltipografo": {
        "name":   "El Tipógrafo",
        "url":    "eltipografo.cl",
        "region": "ohiggins",
        "reason": "Censo marcó \"API live\" pero re-verificación en vivo "
                   "(2026-08-22) encontró que es una SPA Angular servida "
                   "desde AWS API Gateway/CloudFront (\"ng-version\" en el "
                   "HTML, \"x-powered-by: Express\"), no WordPress -- "
                   "/wp-json/ devuelve la misma cáscara HTML que cualquier "
                   "otra ruta. No viable.",
    },
    "rancaguatv": {
        "name":   "Rancagua TV",
        "url":    "rancaguatv.cl",
        "region": "ohiggins",
        "reason": "Censo marcó \"API live\" pero re-verificación en vivo "
                   "(2026-08-22) encontró que /wp-json/wp/v2/posts devuelve "
                   "HTML (200, text/html), no JSON -- la misma cáscara que "
                   "la portada, sin marcadores wp-content en ninguna "
                   "parte. No viable.",
    },
    "elrancahuaso": {
        "name":   "El Rancahuaso",
        "url":    "elrancahuaso.cl",
        "region": "ohiggins",
        "reason": "Censo marcó \"no\" (WordPress) -- /wp-json/ devuelve "
                   "404 tras redirect. CMS propio, no re-investigado más "
                   "a fondo (fuera del alcance de esta pasada, que solo "
                   "re-verificó los \"yes (API live)\").",
    },
    "diarioviregion": {
        "name":   "Diario Sexta Región Online",
        "url":    "diarioviregion.cl",
        "region": "ohiggins",
        "reason": "Censo lo marcó \"inconclusive\" (403 en la portada). "
                   "Re-verificación en vivo (2026-08-22) confirmó CMS "
                   "Joomla (rutas /media/jui/ de Joomla UI), bloqueado por "
                   "Cloudflare (\"Malware detected\") incluso antes de "
                   "llegar a cualquier ruta de contenido. No es WordPress, "
                   "no viable.",
    },
    "pichilemunews": {
        "name":   "PichilemuNews",
        "url":    "pichilemunews.cl",
        "region": "ohiggins",
        "reason": "Censo marcó \"API locked\" -- confirmado en vivo "
                   "2026-08-22: /wp-json/wp/v2/posts devuelve HTTP 403 "
                   "\"No tienes autorización para llevar a cabo esta "
                   "acción\" (WordPress deshabilitó explícitamente la "
                   "REST API). No viable.",
    },
    # ── Araucanía (national expansion) ────────────────────────────────────────
    "radioaraucana": {
        "name":   "Radio Araucana",
        "url":    "radioaraucana.cl",
        "region": "araucania",
        "reason": "Censo marcó \"API locked\" -- confirmado en vivo "
                   "2026-08-22: /wp-json/wp/v2/posts devuelve HTTP 403 "
                   "Forbidden (Cloudflare). No viable.",
    },
    "redinformativa": {
        "name":   "Red Informativa (Villarrica)",
        "url":    "radio.redinformativa.cl",
        "region": "araucania",
        "reason": "Censo marcó \"API live\" -- la API en efecto responde "
                   "200 pero /wp-json/wp/v2/posts tiene X-WP-Total 0: el "
                   "sitio publica sus noticias reales bajo un post type "
                   "personalizado de JetEngine (\"jet-engine\"/\"Listing "
                   "Items\"), no bajo el post type nativo de WordPress. No "
                   "es un caso de instalación vacía, es un modelo de "
                   "contenido no estándar -- necesitaría un scraper a "
                   "medida (como radiopolar.py) para ser viable; no "
                   "justifica la inversión para una sola radio ya cubierta "
                   "indirectamente por otros medios de Villarrica/Pucón en "
                   "esta región.",
    },
    "noticiasdellago": {
        "name":   "Noticias del Lago",
        "url":    "noticiasdellago.cl",
        "region": "araucania",
        "reason": "Censo lo listó como medio propio, pero re-verificación "
                   "en vivo (2026-08-22) encontró que el dominio "
                   "redirecciona (301) directamente a araucanianoticias.cl "
                   "-- no es un medio distinto, es el mismo Araucanía "
                   "Noticias bajo otro dominio/alias. Ya cubierto por "
                   "\"araucanianoticias\", no se registra por separado.",
    },
    "puconradio": {
        "name":   "Pucón Radio",
        "url":    "puconradio.cl",
        "region": "araucania",
        "reason": "Censo marcó \"API live\" pero re-verificación en vivo "
                   "(2026-08-22) encontró un frontend Next.js "
                   "(\"x-powered-by: Next.js\") que devuelve HTML incluso "
                   "en /wp-json/wp/v2/posts -- no hay REST API de "
                   "WordPress accesible en esa ruta. Requeriría un scraper "
                   "a medida (como radiopolar.py); no se investigó más a "
                   "fondo por ahora, no justifica la inversión para una "
                   "sola radio.",
    },
    # ── Maule (national expansion) ────────────────────────────────────────────
    "tv5": {
        "name":   "TV5 Linares",
        "url":    "tv5.cl",
        "region": "maule",
        "reason": "Censo marcó \"API live\" pero re-verificación en vivo "
                   "(2026-08-22) encontró un frontend Next.js "
                   "(\"__NEXT_DATA__\" en el HTML, sitemaps dedicados de "
                   "Google News) -- no es WordPress, /wp-json/ no existe en "
                   "esa ruta. Requeriría un scraper a medida (como "
                   "radiopolar.py); no se investigó más a fondo, no "
                   "justifica la inversión para un solo canal.",
    },
    # ── Biobío (national expansion) ───────────────────────────────────────────
    "radiollacolen": {
        "name":   "Radio Llacolén",
        "url":    "radiollacolen.com",
        "region": "biobio",
        "reason": "Censo marcó \"API live\" pero con 0 posts en la "
                   "consulta -- confirmado en vivo 2026-08-22: X-WP-Total "
                   "0 en el tipo de contenido nativo \"post\", y "
                   "/wp-json/wp/v2/types no expone ningún post type "
                   "personalizado con contenido de noticias (solo post, "
                   "page, attachment, y tipos internos de Elementor). "
                   "Instalación WordPress vacía -- sin contenido real que "
                   "archivar. No viable.",
    },
    # ── Valparaíso (national expansion) ───────────────────────────────────────
    "portalesfm": {
        "name":   "Radio Portales de Valparaíso",
        "url":    "portalesfm.cl",
        "region": "valparaiso",
        "reason": "Censo marcó \"API live\" y la API en efecto responde, "
                   "pero re-verificación en vivo (2026-08-22) encontró que "
                   "los 78 posts indexados son en realidad reproducciones "
                   "de canciones (\"El Deluki - Solito Los 2\", \"Casandra "
                   "Paz - La Vida me Trajo Hasta Aquí\"), todos bajo la "
                   "categoría \"scroll\" -- la categoría \"actualidad\" "
                   "(noticias) existe pero tiene 0 posts. Es un log de "
                   "reproducción musical, no contenido editorial de "
                   "noticias. No viable.",
    },
    # ── Región Metropolitana (national expansion) ──────────────────────────────
    "duplos": {
        "name":   "Duplos",
        "url":    "duplos.cl",
        "region": "metropolitana",
        "reason": "Censo lo marcó borderline (\"general-interest con "
                   "encuadre RM\"). Re-verificación en vivo 2026-08-22 de "
                   "sus 15 posts más recientes lo descarta: farándula "
                   "nacional (Gala Caldirola), resultados SIMCE "
                   "nacionales, encuesta Cadem, política nacional "
                   "(reforma de seguridad del Gobierno), y notas "
                   "policiales de Antofagasta/Osorno/Concepción en el "
                   "mismo feed -- no es prensa local/comunal de la RM en "
                   "la práctica, es un agregador nacional. No viable para "
                   "el alcance de esta campaña.",
    },
    "recoletaaldia": {
        "name":   "Recoleta al Día",
        "url":    "recoleta.cl/diario-digital-recoleta-al-dia",
        "region": "metropolitana",
        "reason": "Boletín digital oficial de la Municipalidad de "
                   "Recoleta, no un medio de prensa independiente -- "
                   "fuera del alcance de esta campaña (mismo criterio "
                   "aplicado a sitios de gobiernos municipales en otras "
                   "regiones). Incluido solo por completitud, ver "
                   "metropolitana.md.",
    },
}

@app.route("/")
def index():
    today_year = datetime.date.today().year
    source_years = {
        sid: list(range(int(db.ARCHIVE_STARTS[sid][:4]), today_year + 1))
        for sid in SOURCES
        if sid in db.ARCHIVE_STARTS
    }
    return render_template("index.html",
                           sources=SOURCES,
                           names=SOURCE_NAMES,
                           source_years=source_years,
                           source_groups=SOURCE_GROUPS,
                           disabled_sources=DISABLED_SOURCES)


@app.route("/source_groups")
def source_groups():
    return jsonify({"groups": SOURCE_GROUPS, "disabled": DISABLED_SOURCES})


@app.route("/source_names")
def source_names():
    return jsonify(SOURCE_NAMES)


@app.route("/status")
def status():
    source_id = request.args.get("source")
    if source_id:
        return jsonify(db.get_status(source_id))
    return jsonify({s: db.get_status(s) for s in SOURCES})


# ── scheduling: nightly on/off + one-off future runs ────────────────────────
# Separate from /archive (which runs a job immediately) -- these just record
# intent. deploy/nightly_archive.py checks nightly_enabled before running a
# source; deploy/scheduler_tick.py (runs every ~10min) picks up due one-off
# runs and actually calls /archive for them.

@app.route("/schedule/state")
def schedule_state():
    return jsonify({
        "nightly_enabled": scheduler_db.all_nightly_states(SOURCES),
        "pending": [r for r in scheduler_db.list_scheduled_runs() if r["status"] == "pending"],
        "recent": [r for r in scheduler_db.list_scheduled_runs(limit=20) if r["status"] != "pending"],
        "nightly_runs": scheduler_db.list_nightly_runs(),
    })


@app.route("/schedule/locks")
def schedule_locks():
    """Every source currently locked by a running job (a manual /archive
    call, the nightly timer, a scheduled run, ovejero_gapfill, etc.) --
    the real "is something actually happening right now" signal, backed
    by the same lock table /archive itself acquires/releases. A lock
    older than LOCK_TTL_MINUTES is annotated stale=True rather than
    hidden -- it means whatever held it died without releasing (a crash,
    a killed process); the next real /archive call on that source will
    reclaim it automatically, this endpoint just makes that visible
    instead of silent."""
    locks = scheduler_db.all_locks()
    now = datetime.datetime.now(datetime.UTC)
    out = {}
    for source_id, info in locks.items():
        try:
            age_min = (now - datetime.datetime.fromisoformat(info["acquired_at"])).total_seconds() / 60
        except Exception:
            age_min = None
        out[source_id] = {
            "holder": info["holder"],
            "acquired_at": info["acquired_at"],
            "age_minutes": round(age_min, 1) if age_min is not None else None,
            "stale": age_min is not None and age_min >= scheduler_db.LOCK_TTL_MINUTES,
        }
    return jsonify(out)


@app.route("/schedule/nightly_run", methods=["POST"])
def schedule_nightly_run_log():
    """Used by deploy/nightly_archive.py to record that a nightly pass
    actually happened (or didn't) -- "what's supposed to run when, and did
    it" is the point of the dashboard; a schedule with no visible outcome
    doesn't answer that."""
    body = request.get_json(force=True, silent=True) or {}
    required = ("started_at", "finished_at", "updated", "failed",
                "skipped_no_data", "skipped_disabled", "detail")
    if not all(k in body for k in required):
        return jsonify({"error": f"body must include {required}"}), 400
    scheduler_db.log_nightly_run(
        body["started_at"], body["finished_at"], body["updated"], body["failed"],
        body["skipped_no_data"], body["skipped_disabled"], body["detail"],
    )
    return jsonify({"ok": True})


@app.route("/schedule/toggle", methods=["POST"])
def schedule_toggle():
    source_id = request.args.get("source")
    enabled = request.args.get("enabled", "1") == "1"
    if not source_id or source_id not in SOURCES:
        return jsonify({"error": "Unknown source"}), 400
    scheduler_db.set_nightly_enabled(source_id, enabled)
    return jsonify({"source": source_id, "nightly_enabled": enabled})


@app.route("/schedule/once", methods=["POST"])
def schedule_once():
    source_id = request.args.get("source")
    mode = request.args.get("mode", "update")
    run_at = request.args.get("run_at")  # ISO 8601, e.g. from <input type=datetime-local>
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None

    if not source_id or source_id not in SOURCES:
        return jsonify({"error": "Unknown source"}), 400
    if not run_at:
        return jsonify({"error": "run_at required (ISO datetime)"}), 400
    try:
        # Accept a bare "YYYY-MM-DDTHH:MM" from datetime-local inputs (no
        # timezone) by treating it as local server time -- consistent with
        # how the nightly timer's own OnCalendar is interpreted.
        datetime.datetime.fromisoformat(run_at)
    except ValueError:
        return jsonify({"error": "run_at must be ISO 8601"}), 400

    new_id = scheduler_db.add_scheduled_run(source_id, mode, run_at, date_from, date_to)
    return jsonify({"id": new_id, "source": source_id, "mode": mode, "run_at": run_at})


@app.route("/schedule/cancel/<int:run_id>", methods=["POST"])
def schedule_cancel(run_id):
    ok = scheduler_db.cancel_scheduled_run(run_id)
    if not ok:
        return jsonify({"error": "Not found or not pending"}), 404
    return jsonify({"id": run_id, "cancelled": True})


@app.route("/schedule/mark/<int:run_id>", methods=["POST"])
def schedule_mark(run_id):
    """Used by deploy/scheduler_tick.py to record the outcome of a scheduled
    run it just executed -- a real endpoint rather than having that
    host-side script reach into the DB file directly, which would silently
    miss (Vault's actual data lives in a Docker volume, not a host path the
    script could import its way into)."""
    status = request.args.get("status")
    note = request.args.get("note")
    if status not in ("done", "error"):
        return jsonify({"error": "status must be done or error"}), 400
    scheduler_db.mark_scheduled_run(run_id, status, note)
    return jsonify({"id": run_id, "status": status})


@app.route("/logs")
def logs():
    """Return the last N lines of the log file."""
    n = int(request.args.get("n", 100))
    if not os.path.exists(_log_file):
        return jsonify({"lines": [], "path": _log_file})
    with open(_log_file, encoding="utf-8") as f:
        lines = f.readlines()
    return jsonify({"lines": lines[-n:], "path": _log_file})


@app.route("/history")
def history():
    source_id = request.args.get("source")
    if not source_id:
        return jsonify({"error": "source required"}), 400
    return jsonify(db.get_scrape_history(source_id))


@app.route("/jobs")
def jobs():
    jobs_dir = os.path.join(os.path.dirname(__file__), "data", "jobs")
    result = []
    if os.path.isdir(jobs_dir):
        for f in sorted(os.listdir(jobs_dir)):
            if f.startswith("yene_") and f.endswith(".json"):
                try:
                    with open(os.path.join(jobs_dir, f), encoding="utf-8") as fh:
                        result.append(json.load(fh))
                except Exception:
                    pass
    return jsonify(result)


@app.route("/archive")
def archive():
    source_id  = request.args.get("source")
    mode       = request.args.get("mode", "update")   # full | update | range
    delay      = float(request.args.get("delay", "1.5"))
    # Optional explicit date range (used for El Pingüino year scraping)
    custom_from = request.args.get("date_from", "").strip()
    custom_to   = request.args.get("date_to", "").strip()

    if not source_id or source_id not in SOURCES:
        return jsonify({"error": "Unknown source"}), 400

    scraper = get_scraper(source_id)
    if not scraper:
        return jsonify({"error": "No scraper for source"}), 400

    today = datetime.date.today().isoformat()

    if custom_from and custom_to:
        date_from = custom_from
        date_to   = custom_to
        mode      = "range"
    elif mode == "full":
        date_from = db.ARCHIVE_STARTS.get(source_id, "2010-01-01")
        date_to   = today
    elif mode == "backfill":
        # Scrape from archive start to the earliest date we already have.
        # Fills historical gaps without re-scraping what's already there.
        status = db.get_status(source_id)
        archive_start = db.ARCHIVE_STARTS.get(source_id, "2010-01-01")
        if status["exists"] and status["min_date"] and status["min_date"] > archive_start:
            date_from = archive_start
            date_to   = status["min_date"]  # up to (not past) what we already have
        else:
            date_from = archive_start
            date_to   = today
    else:  # update
        date_from = db.get_update_start(source_id)
        date_to   = today

    db.init_db(source_id)
    job_id = db.log_start(source_id, mode, date_from, date_to)

    def generate():
        # Thin wrapper: same per-source lock /repair uses, so the nightly
        # timer, a one-off scheduled run, and a repair pass can never work
        # the same source at once. See scheduler_db.py's source_locks note.
        if not scheduler_db.lock_acquire(source_id, holder=f"archive:{mode}"):
            held = scheduler_db.lock_status(source_id)
            yield _sse({"type": "log", "level": "error",
                        "msg": f"{source_id} is locked by "
                               f"'{held and held['holder']}' right now -- skipping"})
            yield _sse({"type": "done", "seen": 0, "saved": 0, "total_db": 0,
                        "min_date": None, "max_date": None, "size_mb": 0,
                        "coverage": {}, "job_status": "locked"})
            return
        try:
            yield from _generate_archive()
        finally:
            scheduler_db.lock_release(source_id)

    def _generate_archive():
        label = f"{mode.upper()} {source_id}  {date_from} → {date_to}"
        yield _sse({"type": "log", "level": "info", "msg": f"🐋 {label}"})

        batch          = []
        BATCH_SIZE     = 50
        total_seen     = 0
        total_saved    = 0
        total_expected = 0
        job_status     = "done"
        failed_pages   = []
        started_at     = datetime.datetime.utcnow()
        last_yield     = [started_at]

        def maybe_heartbeat():
            """Yield a keepalive ping if nothing has been sent in the last 5s."""
            now = datetime.datetime.utcnow()
            if (now - last_yield[0]).seconds >= 5:
                last_yield[0] = now
                return _sse({"type": "heartbeat"})
            return None

        def progress_payload():
            elapsed = (datetime.datetime.utcnow() - started_at).total_seconds()
            rate    = total_seen / elapsed if elapsed > 0 else 0
            eta     = ((total_expected - total_seen) / rate) if (rate > 0 and total_expected) else 0
            return {
                "type":     "progress",
                "seen":     total_seen,
                "saved":    total_saved,
                "total":    total_expected,
                "elapsed":  round(elapsed),
                "rate":     round(rate, 2),
                "eta":      round(eta),
            }

        try:
            for event in scraper.run(query="", date_from=date_from,
                                     date_to=date_to, delay=delay):
                hb = maybe_heartbeat()
                if hb:
                    yield hb
                    last_yield[0] = datetime.datetime.utcnow()

                if event.get("type") == "article":
                    batch.append(event["data"])
                    total_seen += 1
                    if len(batch) >= BATCH_SIZE:
                        ins, _ = db.insert_articles(source_id, batch)
                        total_saved += ins
                        batch = []
                        last_yield[0] = datetime.datetime.utcnow()
                        yield _sse(progress_payload())
                elif event.get("type") == "total":
                    total_expected = event.get("n", 0)
                    last_yield[0] = datetime.datetime.utcnow()
                    yield _sse(progress_payload())
                elif event.get("type") == "log":
                    last_yield[0] = datetime.datetime.utcnow()
                    yield _sse(event)
                elif event.get("type") == "fail":
                    yield _sse({"type": "log", "level": "warn",
                                "msg": f"  ✗ {event.get('url','')}"})
                elif event.get("type") == "failed_pages":
                    failed_pages.extend(event.get("pages", []))
                    last_yield[0] = datetime.datetime.utcnow()
                    yield _sse({"type": "log", "level": "warn", "msg": event["msg"]})
        except GeneratorExit:
            job_status = "stopped"
        except Exception as e:
            app.logger.exception("Scraper error for %s", source_id)
            job_status = "error"
            yield _sse({"type": "log", "level": "error", "msg": str(e)})

        if batch:
            ins, _ = db.insert_articles(source_id, batch)
            total_saved += ins

        note = f"failed pages: {failed_pages}" if failed_pages else ""
        db.log_end(job_id, source_id, job_status, total_seen, total_saved, note=note)

        status = db.get_status(source_id)

        # write companion JSON for cleaner to discover
        jobs_dir = os.path.join(os.path.dirname(__file__), "data", "jobs")
        os.makedirs(jobs_dir, exist_ok=True)
        job_meta = {
            "created_at":  datetime.datetime.utcnow().isoformat() + "Z",
            "source_id":   source_id,
            "source_name": SOURCE_NAMES.get(source_id, source_id),
            "mode":        mode,
            "date_from":   date_from,
            "date_to":     date_to,
            "job_status":  job_status,
            "n_seen":      total_seen,
            "n_saved":     total_saved,
            "total_db":    status["count"],
            "min_date":    status["min_date"],
            "max_date":    status["max_date"],
            "coverage":    status["coverage"],
        }
        jid = uuid.uuid4().hex[:8]
        jpath = os.path.join(jobs_dir, f"yene_{source_id}_{jid}.json")
        with open(jpath, "w", encoding="utf-8") as jf:
            json.dump(job_meta, jf, ensure_ascii=False, indent=2)
        # A generator must not yield again after GeneratorExit was raised into
        # it (Python enforces this -- yielding here throws "generator ignored
        # GeneratorExit", confirmed live 2026-08-22 when a disconnected client
        # left ovejeronoticias's job crashing at cleanup instead of exiting
        # cleanly). The client that triggered "stopped" is already gone, so
        # there's nothing to yield to anyway -- db writes above still ran.
        if job_status != "stopped":
            yield _sse({
                "type":     "done",
                "seen":     total_seen,
                "saved":    total_saved,
                "total_db": status["count"],
                "min_date": status["min_date"],
                "max_date": status["max_date"],
                "size_mb":  status["size_mb"],
                "coverage": status["coverage"],
                "job_status": job_status,
            })

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── repair: fix already-stored bad body_text in place (added 2026-08-10) ────
# /archive re-running a date range does NOT fix existing rows -- inserts are
# INSERT OR IGNORE, so a URL that's already there (even with a bad body)
# just gets silently skipped. This is a real UPDATE path instead. Bounded by
# `limit` per call on purpose -- call it repeatedly (see
# deploy/elpinguino_repair.py) rather than trying to fix everything in one
# unbounded request.
#
# Only sources whose scraper exposes a single-URL _fetch_body() can use
# this (currently just El Pingüino, the one this was built for) --
# WordPress-based sources get their full body straight from the REST API in
# one shot and don't have (or need) a per-article re-fetch path.
REPAIRABLE_SOURCES = {"elpinguino"}


@app.route("/repair")
def repair():
    source_id = request.args.get("source")
    limit = int(request.args.get("limit", 200))
    section = request.args.get("section", "").strip() or None

    if source_id not in REPAIRABLE_SOURCES:
        return jsonify({"error": f"'{source_id}' doesn't support /repair "
                                  f"(only: {sorted(REPAIRABLE_SOURCES)})"}), 400

    scraper = get_scraper(source_id)
    if not scraper or not hasattr(scraper, "_fetch_body"):
        return jsonify({"error": "scraper has no single-URL fetch method"}), 400

    db.init_db(source_id)  # runs the repair_checked_at migration if not already applied

    def generate():
        if not scheduler_db.lock_acquire(source_id, holder="repair"):
            held_by = scheduler_db.lock_status(source_id)
            yield _sse({"type": "log", "level": "error",
                        "msg": f"{source_id} is locked by '{held_by and held_by['holder']}' "
                               f"right now -- try later"})
            yield _sse({"type": "done", "checked": 0, "improved": 0, "remaining": None})
            return
        try:
            batch = db.get_unrepaired_short_articles(source_id, limit=limit, section=section)
            remaining_before = db.count_unrepaired_short(source_id, section=section)
            scope = f" (section={section})" if section else ""
            yield _sse({"type": "log", "level": "info",
                        "msg": f"🔧 Repair batch{scope}: {len(batch)} articles "
                               f"({remaining_before} total still unrepaired{scope})"})

            # Same bounded-thread-pool pattern as elpinguino's bulk fetch --
            # single-URL fetches through the scraper's own shared session,
            # already measured safe at this worker count (see BULK_WORKERS).
            workers = getattr(scraper, "BULK_WORKERS", 1)
            checked, improved = 0, 0
            with cf.ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(scraper._fetch_body, art["url"], 1.5): art
                    for art in batch
                }
                for fut in cf.as_completed(futures):
                    art = futures[fut]
                    result = fut.result()
                    new_body = result[3] if result else ""
                    new_image = result[4] if result else ""
                    did_improve = db.apply_repair_result(source_id, art["id"], new_body, new_image)
                    checked += 1
                    if did_improve:
                        improved += 1
                    yield _sse({
                        "type": "progress", "checked": checked, "total": len(batch),
                        "improved": improved, "url": art["url"],
                    })

            remaining_after = db.count_unrepaired_short(source_id, section=section)
            yield _sse({
                "type": "done", "checked": checked, "improved": improved,
                "remaining": remaining_after,
            })
            yield _sse({"type": "log", "level": "info",
                        "msg": f"✓ Repair batch done: {improved}/{checked} improved, "
                               f"{remaining_after} still left{scope}"})
        finally:
            scheduler_db.lock_release(source_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── image file backfill (added 2026-08-10) ───────────────────────────────────
# Generic across any source with data (unlike /repair, which needs a
# scraper-specific single-URL body fetch) -- this just downloads whatever
# image_url values already exist. See vault/images.py.

@app.route("/images/backfill")
def images_backfill():
    source_id = request.args.get("source")
    limit = int(request.args.get("limit", 200))

    if not source_id or source_id not in SOURCES:
        return jsonify({"error": "Unknown source"}), 400

    db.init_db(source_id)

    def generate():
        if not scheduler_db.lock_acquire(source_id, holder="images"):
            held = scheduler_db.lock_status(source_id)
            yield _sse({"type": "log", "level": "error",
                        "msg": f"{source_id} is locked by "
                               f"'{held and held['holder']}' right now -- try later"})
            yield _sse({"type": "done", "checked": 0, "downloaded": 0, "remaining": None})
            return
        try:
            import images as images_mod
            batch = db.get_articles_missing_image_file(source_id, limit=limit)
            remaining_before = db.count_missing_image_files(source_id)
            yield _sse({"type": "log", "level": "info",
                        "msg": f"🖼 Image batch: {len(batch)} articles "
                               f"({remaining_before} total still missing)"})

            checked, downloaded = 0, 0
            for art in batch:
                local_path = images_mod.download_image(art["image_url"])
                db.set_image_result(source_id, art["id"], local_path)
                checked += 1
                if local_path:
                    downloaded += 1
                yield _sse({
                    "type": "progress", "checked": checked, "total": len(batch),
                    "downloaded": downloaded, "url": art["image_url"],
                })

            remaining_after = db.count_missing_image_files(source_id)
            yield _sse({
                "type": "done", "checked": checked, "downloaded": downloaded,
                "remaining": remaining_after,
            })
            yield _sse({"type": "log", "level": "info",
                        "msg": f"✓ Image batch done: {downloaded}/{checked} downloaded, "
                               f"{remaining_after} still left"})
        finally:
            scheduler_db.lock_release(source_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── author backfill (added 2026-08-11) ───────────────────────────────────────
# Existing rows predate the fix that started requesting WordPress's own
# author field (see scrapers/wordpress.py). No per-article re-fetch needed --
# sweeps cheap listing pages (url + author only) and UPDATEs by url. Only
# WordPress-based scrapers expose run_author_backfill().

@app.route("/authors/backfill")
def authors_backfill():
    source_id = request.args.get("source")
    if not source_id or source_id not in SOURCES:
        return jsonify({"error": "Unknown source"}), 400

    scraper = get_scraper(source_id)
    if not scraper or not hasattr(scraper, "run_author_backfill"):
        return jsonify({"error": f"'{source_id}' scraper has no run_author_backfill()"}), 400

    db.init_db(source_id)

    def generate():
        if not scheduler_db.lock_acquire(source_id, holder="authors"):
            held = scheduler_db.lock_status(source_id)
            yield _sse({"type": "log", "level": "error",
                        "msg": f"{source_id} is locked by "
                               f"'{held and held['holder']}' right now -- try later"})
            yield _sse({"type": "done", "checked": 0, "updated": 0, "remaining": None})
            return
        try:
            missing_before = db.count_missing_author(source_id)
            yield _sse({"type": "log", "level": "info",
                        "msg": f"👤 Author backfill starting ({missing_before} missing)"})

            checked, updated = 0, 0
            for ev in scraper.run_author_backfill(delay=1.0):
                if ev["type"] == "log":
                    yield _sse(ev)
                elif ev["type"] == "page":
                    pairs = ev["pairs"]
                    checked += len(pairs)
                    updated += db.update_authors_bulk(source_id, pairs)
                    yield _sse({
                        "type": "progress", "checked": checked,
                        "page": ev["page"], "total_pages": ev["total_pages"],
                        "updated": updated,
                    })

            missing_after = db.count_missing_author(source_id)
            yield _sse({
                "type": "done", "checked": checked, "updated": updated,
                "remaining": missing_after,
            })
            yield _sse({"type": "log", "level": "info",
                        "msg": f"✓ Author backfill done: {updated} rows updated, "
                               f"{missing_after} still missing"})
        finally:
            scheduler_db.lock_release(source_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── explorer: simple search/browse UI (added 2026-08-11) ────────────────────

@app.route("/explore")
def explore():
    return render_template(
        "explore.html", sources=EXPLORE_SOURCES, names=SOURCE_NAMES,
    )


def _fts_query(q, title_only):
    """FTS5 column filter -- restricts the match to the title column instead
    of title+body_text. Parenthesized so multi-word/phrase queries stay
    grouped under the filter instead of only the first term being scoped."""
    if q and title_only:
        return f"title:({q})"
    return q


def _parse_source_param():
    """`source` accepts "all", a single id, or a comma-separated list of
    ids (added for the region-checkbox multi-select in index2.html's
    explorer) -- returns (source_ids_list, error_response_or_None)."""
    raw = request.args.get("source", "all")
    if raw == "all":
        return list(EXPLORE_SOURCES), None
    ids = [s for s in raw.split(",") if s]
    unknown = [s for s in ids if s not in EXPLORE_SOURCES]
    if unknown:
        return None, (jsonify({"error": f"Unknown source(s): {', '.join(unknown)}"}), 400)
    return ids, None


@app.route("/api/search")
def api_search():
    source_ids, err = _parse_source_param()
    if err:
        return err

    q = request.args.get("q", "").strip()
    title_only = request.args.get("title_only", "").lower() in ("1", "true", "on")
    q = _fts_query(q, title_only)
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    limit = min(int(request.args.get("limit", 25)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    try:
        rows, total = db.search_all_sources(q, date_from, date_to, limit, offset,
                                              source_ids=source_ids)
    except Exception as e:
        # Most likely an invalid FTS5 query syntax (unbalanced quotes etc.)
        return jsonify({"error": f"Search error: {e}"}), 400

    for r in rows:
        # Trim body_text for the list view -- full text is fetched on expand,
        # no need to ship 190KB articles for every row in a page of results.
        r["snippet"] = (r["body_text"] or "")[:280]
        del r["body_text"]

    return jsonify({"rows": rows, "total": total, "limit": limit, "offset": offset})


# CSV cells that are bulletproof against weak/non-RFC4180 readers: no embedded
# newlines (elpinguino's body_text can carry raw newlines -- its own extraction
# doesn't collapse whitespace the way the shared WordPress-scraper path does),
# no control characters (stray NULs etc. from bad scrapes truncate a cell in
# some readers), and no leading =/+/-/@ (Excel/Sheets formula injection).
_CSV_FORMULA_LEADCHARS = ("=", "+", "-", "@")


def _csv_field(val):
    s = "" if val is None else str(val)
    s = re.sub(r"\s+", " ", s).strip()
    s = "".join(c for c in s if c == " " or ord(c) >= 32)
    if s[:1] in _CSV_FORMULA_LEADCHARS:
        s = " " + s
    return s


@app.route("/api/export.csv")
def api_export_csv():
    source_ids, err = _parse_source_param()
    if err:
        return err

    q = request.args.get("q", "").strip()
    title_only = request.args.get("title_only", "").lower() in ("1", "true", "on")
    q = _fts_query(q, title_only)
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    def generate():
        import csv, io
        buf = io.StringIO()
        # QUOTE_ALL: every field gets wrapped in quotes regardless of content,
        # so even a naive/non-RFC4180 CSV reader has an unambiguous field
        # boundary to look for instead of relying on it correctly tracking
        # quote state across an embedded comma or newline.
        writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        # UTF-8 BOM -- without it, Excel on Windows guesses the system
        # codepage instead of UTF-8 and mangles the accented Spanish text.
        yield "﻿"
        writer.writerow(["source_id", "source_name", "date", "title", "author", "section", "url", "body_text"])
        yield buf.getvalue()
        for sid in source_ids:
            for a in db.iter_matching_articles(sid, q, date_from, date_to):
                buf.seek(0)
                buf.truncate(0)
                writer.writerow([_csv_field(a["source_id"]), _csv_field(a["source"]),
                                  _csv_field(a["date"]), _csv_field(a["title"]),
                                  _csv_field(a.get("author", "")),
                                  _csv_field(a["section"]), _csv_field(a["url"]),
                                  _csv_field(a["body_text"])])
                yield buf.getvalue()

    if set(source_ids) == set(EXPLORE_SOURCES):
        fname_bit = "todas-las-fuentes"
    elif len(source_ids) == 1:
        fname_bit = source_ids[0]
    else:
        fname_bit = f"{len(source_ids)}-fuentes"
    filename = f"camplux_{fname_bit}_{datetime.date.today().isoformat()}.csv"
    return Response(
        stream_with_context(generate()),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/api/article/<source_id>/<int:article_id>")
def api_article(source_id, article_id):
    if source_id not in SOURCES:
        return jsonify({"error": "Unknown source"}), 400
    con = db.connect(source_id)
    row = con.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    con.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@app.route("/api/image/<path:rel_path>")
def api_image(rel_path):
    # rel_path looks like "images/ab/abcd1234....jpg" -- images.py always
    # writes under vault/data/images/, so require that prefix and let
    # send_from_directory's own normalisation refuse any ../ escape attempt.
    if not rel_path.startswith("images/"):
        abort(404)
    return send_from_directory(db.DATA_DIR, rel_path)


def _sse(data):
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    # waitress, not Flask's dev server: debug=True exposes an interactive
    # Python console on unhandled exceptions -- fine on localhost-only, a
    # real problem once this is reachable beyond localhost.
    serve(app, host="0.0.0.0", port=5001, threads=4)
