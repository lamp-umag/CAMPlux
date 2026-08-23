"""
Downloads missing images for every source with data, region by region
(same population order as historical_backfill_campaign.py, magallanes
first since it's the flagship, then nacional/regional/internacional).

Confirmed live 2026-08-22: only ~1.4% of articles across the whole
archive have a downloaded image (108 of 118 sources had literally never
attempted one), and that was before the historical backfill campaign
roughly doubled the article count -- this is a large, genuinely
long-running job (potentially 1M+ images, one HTTP request each), not a
quick pass. Expect this to run for a long time; that's fine, it's meant
to just keep going in the background.

/images/backfill is bounded to `limit` articles per call (200 by
default) -- this script loops that call per source until its own
"remaining" count hits 0, or gives up on that source (temporarily) if a
few consecutive calls make no progress at all (site blocking us, dead
image URLs, etc.) and moves on, leaving it for a later pass rather than
spinning forever on one stuck source.

Runs alongside historical_backfill_campaign.py -- both only ever touch
one source's lock at a time via the same scheduler_db mechanism /archive
already uses, so if they want the same source simultaneously one just
skips it this round and retries later rather than fighting over it.

Progress persisted to deploy/logs_image_backfill.log and
deploy/.image_backfill_progress.json (gitignored), resumable.

Usage: python3 deploy/image_backfill_campaign.py
"""
import datetime
import json
import os
import threading
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRESS_PATH = os.path.join(HERE, ".image_backfill_progress.json")

VAULT_BASE = "http://127.0.0.1:5001"
BATCH_SIZE = 3
PAUSE_BETWEEN_BATCHES_S = 15
CALL_LIMIT = 200
MAX_NO_PROGRESS_CALLS = 3  # give up on a source (for this pass) after this
                            # many consecutive calls download 0 new images
PER_CALL_TIMEOUT_S = 600

REGION_ORDER = [
    "magallanes",
    "aysen", "arica_parinacota", "atacama", "tarapaca", "los_rios",
    "nuble", "antofagasta", "coquimbo", "los_lagos", "ohiggins",
    "araucania", "maule", "biobio", "valparaiso", "metropolitana",
    "nacional", "regional", "internacional",
]

_log_lock = threading.Lock()


def log(msg):
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    with _log_lock:
        print(line, flush=True)


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_PATH, "w") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def build_queue():
    groups = requests.get(f"{VAULT_BASE}/source_groups", timeout=15).json()
    queue = []
    seen = set()
    for region in REGION_ORDER:
        for sid in groups["groups"].get(region, {}).get("sources", []):
            if sid not in seen:
                queue.append((region, sid))
                seen.add(sid)
    return queue


def backfill_one_source(region, source_id, results):
    total_downloaded = 0
    no_progress_streak = 0
    calls = 0
    t0 = time.time()
    while True:
        calls += 1
        try:
            r = requests.get(f"{VAULT_BASE}/images/backfill",
                              params={"source": source_id, "limit": CALL_LIMIT},
                              stream=True, timeout=PER_CALL_TIMEOUT_S)
            last_done = None
            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                try:
                    evt = json.loads(raw_line[len("data: "):])
                except ValueError:
                    continue
                if evt.get("type") == "log" and "locked by" in evt.get("msg", ""):
                    results[source_id] = {"status": "locked", "downloaded": total_downloaded,
                                           "elapsed_s": round(time.time() - t0)}
                    log(f"  ⚠ {source_id}: bloqueado por otro proceso ahora, se reintentará otra vez")
                    return
                if evt.get("type") == "done":
                    last_done = evt
        except Exception as e:
            results[source_id] = {"status": "error", "note": str(e), "downloaded": total_downloaded,
                                   "elapsed_s": round(time.time() - t0)}
            log(f"  ✗ {source_id}: error tras {calls} llamada(s) -- {e}")
            return

        if last_done is None:
            results[source_id] = {"status": "error", "note": "no done event",
                                   "downloaded": total_downloaded, "elapsed_s": round(time.time() - t0)}
            log(f"  ✗ {source_id}: sin evento final")
            return

        downloaded_this_call = last_done.get("downloaded", 0)
        total_downloaded += downloaded_this_call
        remaining = last_done.get("remaining")

        if downloaded_this_call == 0:
            no_progress_streak += 1
        else:
            no_progress_streak = 0

        if remaining == 0:
            results[source_id] = {"status": "done", "downloaded": total_downloaded,
                                   "calls": calls, "elapsed_s": round(time.time() - t0)}
            log(f"  ✓ {source_id}: completo -- {total_downloaded} imágenes descargadas en {calls} llamada(s)")
            return

        if no_progress_streak >= MAX_NO_PROGRESS_CALLS:
            results[source_id] = {"status": "stuck", "downloaded": total_downloaded,
                                   "remaining": remaining, "calls": calls,
                                   "elapsed_s": round(time.time() - t0)}
            log(f"  ⚠ {source_id}: {no_progress_streak} llamadas seguidas sin descargar nada "
                f"({remaining} restantes) -- se deja para otra pasada")
            return
        # else: real progress being made, keep looping this source


def main():
    progress = load_progress()
    queue = build_queue()
    log(f"=== Image backfill campaign starting. {len(queue)} sources total. ===")

    pending = [(region, sid) for region, sid in queue if progress.get(sid, {}).get("status") != "done"]
    log(f"{len(queue) - len(pending)} already marked done, {len(pending)} left to check.")

    current_region = None
    i = 0
    while i < len(pending):
        batch = pending[i:i + BATCH_SIZE]
        i += BATCH_SIZE

        if batch[0][0] != current_region:
            current_region = batch[0][0]
            log(f"--- región/grupo: {current_region} ---")

        log(f"Batch: {[sid for _, sid in batch]}")
        results = {}
        threads = [threading.Thread(target=backfill_one_source, args=(region, sid, results))
                   for region, sid in batch]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for sid, outcome in results.items():
            outcome["checked_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            progress[sid] = outcome
        save_progress(progress)

        if i < len(pending):
            log(f"Pausa de {PAUSE_BETWEEN_BATCHES_S}s antes del siguiente lote…")
            time.sleep(PAUSE_BETWEEN_BATCHES_S)

    done = sum(1 for v in progress.values() if v.get("status") == "done")
    stuck = sum(1 for v in progress.values() if v.get("status") == "stuck")
    errors = sum(1 for v in progress.values() if v.get("status") == "error")
    locked = sum(1 for v in progress.values() if v.get("status") == "locked")
    total_downloaded = sum(v.get("downloaded", 0) for v in progress.values())
    log(f"=== Pass complete. done={done} stuck={stuck} errors={errors} locked={locked} "
        f"total_downloaded={total_downloaded} ===")
    if stuck or errors or locked:
        log("Re-run this script to retry anything not 'done' -- completed sources are skipped automatically.")


if __name__ == "__main__":
    main()
