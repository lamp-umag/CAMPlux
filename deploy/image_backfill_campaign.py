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
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRESS_PATH = os.path.join(HERE, ".image_backfill_progress.json")

VAULT_BASE = "http://127.0.0.1:5001"
BATCH_SIZE = 3  # concurrent worker pool size, see main()
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


def backfill_one_source(region, source_id):
    """Runs to completion (or gives up) for one source, entirely on its own
    thread -- returns its outcome dict rather than writing into shared
    state, so the caller can use a rolling worker pool instead of waiting
    for a fixed batch. A source with a huge backlog (elpinguino: ~190k
    missing images) can legitimately take hours; with a rolling pool that
    only ties up one of the worker slots instead of blocking everyone
    else in a fixed batch until the slowest one finishes."""
    total_downloaded = 0
    no_progress_streak = 0
    calls = 0
    t0 = time.time()
    log(f"  ▶ {source_id} ({region}): iniciando")
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
                    log(f"  ⚠ {source_id}: bloqueado por otro proceso ahora, se reintentará otra vez")
                    return source_id, {"status": "locked", "downloaded": total_downloaded,
                                        "elapsed_s": round(time.time() - t0)}
                if evt.get("type") == "done":
                    last_done = evt
        except Exception as e:
            log(f"  ✗ {source_id}: error tras {calls} llamada(s) -- {e}")
            return source_id, {"status": "error", "note": str(e), "downloaded": total_downloaded,
                                "elapsed_s": round(time.time() - t0)}

        if last_done is None:
            log(f"  ✗ {source_id}: sin evento final")
            return source_id, {"status": "error", "note": "no done event",
                                "downloaded": total_downloaded, "elapsed_s": round(time.time() - t0)}

        downloaded_this_call = last_done.get("downloaded", 0)
        total_downloaded += downloaded_this_call
        remaining = last_done.get("remaining")

        if downloaded_this_call == 0:
            no_progress_streak += 1
        else:
            no_progress_streak = 0

        if remaining == 0:
            log(f"  ✓ {source_id}: completo -- {total_downloaded} imágenes descargadas en {calls} llamada(s)")
            return source_id, {"status": "done", "downloaded": total_downloaded,
                                "calls": calls, "elapsed_s": round(time.time() - t0)}

        if no_progress_streak >= MAX_NO_PROGRESS_CALLS:
            log(f"  ⚠ {source_id}: {no_progress_streak} llamadas seguidas sin descargar nada "
                f"({remaining} restantes) -- se deja para otra pasada")
            return source_id, {"status": "stuck", "downloaded": total_downloaded,
                                "remaining": remaining, "calls": calls,
                                "elapsed_s": round(time.time() - t0)}
        # else: real progress being made, keep looping this source


def main():
    progress = load_progress()
    queue = build_queue()
    log(f"=== Image backfill campaign starting. {len(queue)} sources total. ===")

    pending = [(region, sid) for region, sid in queue if progress.get(sid, {}).get("status") != "done"]
    log(f"{len(queue) - len(pending)} already marked done, {len(pending)} left to check.")
    log(f"Rolling pool of {BATCH_SIZE} workers -- a big source (e.g. elpinguino, ~190k missing "
        f"images) ties up one slot for a long time without blocking the other two from moving "
        f"on to the next source in the queue, unlike a fixed batch-of-3-then-wait approach.")

    # Submit everything up front; ThreadPoolExecutor's own internal queue
    # feeds each freed worker the next pending item automatically -- this
    # IS the rolling-pool behavior, no manual batching needed.
    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
        futures = {pool.submit(backfill_one_source, region, sid): sid for region, sid in pending}
        for future in as_completed(futures):
            sid, outcome = future.result()
            outcome["checked_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            progress[sid] = outcome
            save_progress(progress)

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
