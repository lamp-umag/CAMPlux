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

# Explorer, for now, only surfaces Magallanes press -- excludes "nacional",
# "regional" (other regions), and "internacional". User request
# 2026-08-11, scoped to /explore only; scraping/archiving still covers
# all of SOURCES. Revert by setting this back to SOURCES.
EXPLORE_SOURCES = tuple(SOURCE_GROUPS["magallanes"]["sources"])

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


# ── explorer: simple search/browse UI (added 2026-08-11) ────────────────────

@app.route("/explore")
def explore():
    return render_template(
        "explore.html", sources=EXPLORE_SOURCES, names=SOURCE_NAMES,
    )


@app.route("/api/search")
def api_search():
    source_id = request.args.get("source", "all")
    if source_id != "all" and source_id not in EXPLORE_SOURCES:
        return jsonify({"error": "Unknown source"}), 400

    q = request.args.get("q", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    limit = min(int(request.args.get("limit", 25)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    try:
        if source_id == "all":
            rows, total = db.search_all_sources(q, date_from, date_to, limit, offset,
                                                  source_ids=EXPLORE_SOURCES)
        else:
            rows, total = db.search_articles(source_id, q, date_from, date_to, limit, offset)
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
    source_id = request.args.get("source", "all")
    if source_id != "all" and source_id not in EXPLORE_SOURCES:
        return jsonify({"error": "Unknown source"}), 400

    q = request.args.get("q", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    source_ids = list(EXPLORE_SOURCES) if source_id == "all" else [source_id]

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
        writer.writerow(["source_id", "source_name", "date", "title", "section", "url", "body_text"])
        yield buf.getvalue()
        for sid in source_ids:
            for a in db.iter_matching_articles(sid, q, date_from, date_to):
                buf.seek(0)
                buf.truncate(0)
                writer.writerow([_csv_field(a["source_id"]), _csv_field(a["source"]),
                                  _csv_field(a["date"]), _csv_field(a["title"]),
                                  _csv_field(a["section"]), _csv_field(a["url"]),
                                  _csv_field(a["body_text"])])
                yield buf.getvalue()

    fname_bit = source_id if source_id != "all" else "todas-las-fuentes"
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
