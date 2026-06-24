import json
import datetime
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from flask import Flask, Response, jsonify, render_template, request
from flask import stream_with_context

import db
from scrapers import get_scraper

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
        "region": "regional",
        "reason": "CMS propio sin WP API confirmada",
    },
    "mercuriovalpo": {
        "name":   "El Mercurio de Valparaíso",
        "url":    "mercuriovalpo.cl",
        "region": "regional",
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


@app.route("/status")
def status():
    source_id = request.args.get("source")
    if source_id:
        return jsonify(db.get_status(source_id))
    return jsonify({s: db.get_status(s) for s in SOURCES})


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


def _sse(data):
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    app.run(debug=True, port=5001, threaded=True)
