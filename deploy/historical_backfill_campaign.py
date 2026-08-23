"""
Full historical backfill for every source added during the national
expansion campaign (see deploy/expansion/) that hasn't gotten one yet.

Phase-2 verification only ever ran a narrow ~3-week mode=range test per
source to confirm it works -- confirmed live 2026-08-22 via the new
/api/source_completeness endpoint that this left the large majority of
the 93 new sources with only that narrow window archived, not their real
available history (some sites have 200k+ posts sitting completely
unarchived, e.g. g5noticias: 2,755 of 218,873). A handful of sources
already got a real mode=full during phase 2 (the "dormant-but-real"
ones, detected because their narrow test came back empty) -- this script
detects and skips those automatically (min_date already <= archive_start)
rather than re-running them.

Paced deliberately per explicit user instruction ("go little by little...
do 3 of them, wait, see how they go, keep iterating"), not a blind mass
launch: never more than BATCH_SIZE sources running at once, region by
region in the same smallest-to-biggest population order as the rest of
the campaign. Uses a rolling worker pool (ThreadPoolExecutor), not fixed
batch-then-wait-for-all-three -- confirmed live 2026-08-23 that job size
varies wildly (some sources: under a minute; others: 3000+ seconds), so a
fixed batch left two workers sitting idle for up to an hour waiting on
the third instead of picking up the next source. A rolling pool keeps the
same "never more than 3 at once" safety property while not wasting that
idle time. Re-checks each source's own current state (not the state when
this script started) before deciding to skip it -- safe to re-run, safe
if the user or another process backfills something manually in the
meantime ("I might have started some before"). Skips anything currently
locked (someone/something else already working on it) rather than
fighting over it.

Progress is persisted per-source outcome in
deploy/logs_historical_backfill.log and a JSON summary in
deploy/.historical_backfill_progress.json (gitignored, same treatment as
ovejero_gapfill's progress marker) so "what worked and what didn't" is
never just in this process's stdout -- readable cold by a future session.

Usage:
    python3 deploy/historical_backfill_campaign.py [--now]

No sleep gate by default (unlike ovejero_gapfill/quality_check) -- this
was launched interactively mid-session, not meant to wait for a quiet
overnight window. --now is accepted anyway for consistency/no-op.
"""
import datetime
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRESS_PATH = os.path.join(HERE, ".historical_backfill_progress.json")
LOG_PATH = os.path.join(HERE, "logs_historical_backfill.log")

VAULT_BASE = "http://127.0.0.1:5001"
BATCH_SIZE = 3  # concurrent worker pool size, see main()
PER_SOURCE_TIMEOUT_S = 3 * 3600  # a single big mode=full (e.g. g5noticias'
                                  # 218k posts) can legitimately run for
                                  # hours -- generous ceiling, not a tight one

# Same population order as deploy/expansion/PLAN.md, smallest region first.
REGION_ORDER = [
    "aysen", "arica_parinacota", "atacama", "tarapaca", "los_rios",
    "nuble", "antofagasta", "coquimbo", "los_lagos", "ohiggins",
    "araucania", "maule", "biobio", "valparaiso", "metropolitana",
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
    """Ordered (region, source_id) list -- region by region, population
    order, skipping DISABLED_SOURCES entirely."""
    groups = requests.get(f"{VAULT_BASE}/source_groups", timeout=15).json()
    queue = []
    for region in REGION_ORDER:
        for sid in groups["groups"].get(region, {}).get("sources", []):
            queue.append((region, sid))
    return queue


def needs_backfill(source_id):
    """Re-checks live status right before deciding -- not a snapshot taken
    once at startup. A source counts as already-done if our min_date has
    already reached (or passed) its own ARCHIVE_STARTS estimate. Also
    returns False (skip) if it's currently locked by anything else."""
    status = requests.get(f"{VAULT_BASE}/status", params={"source": source_id}, timeout=15).json()
    if not status.get("exists"):
        return True, "sin datos, necesita full"
    min_d, arch_start = status.get("min_date"), status.get("archive_start")
    if min_d and arch_start and min_d <= arch_start:
        return False, f"ya completo (min_date {min_d} <= archive_start {arch_start})"

    locks = requests.get(f"{VAULT_BASE}/schedule/locks", timeout=15).json()
    if source_id in locks:
        held = locks[source_id]
        return False, f"ocupado ahora mismo por '{held['holder']}' -- no interferir"

    return True, f"min_date actual {min_d}, archive_start esperado {arch_start}"


def run_one_backfill(region, source_id):
    url = f"{VAULT_BASE}/archive"
    params = {"source": source_id, "mode": "full", "delay": "1.0"}
    t0 = time.time()
    log(f"  ▶ {source_id} ({region}): iniciando mode=full")
    try:
        with requests.get(url, params=params, stream=True, timeout=PER_SOURCE_TIMEOUT_S) as r:
            last_done = None
            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                try:
                    evt = json.loads(raw_line[len("data: "):])
                except ValueError:
                    continue
                if evt.get("type") == "done":
                    last_done = evt
            elapsed = time.time() - t0
            if last_done is None:
                log(f"  ✗ {source_id}: sin evento final tras {elapsed:.0f}s")
                return source_id, {"status": "error", "note": "stream ended without a done event",
                                    "elapsed_s": round(elapsed)}
            elif last_done.get("job_status") == "locked":
                log(f"  ⚠ {source_id}: bloqueado por otro proceso, se reintentará otra vez")
                return source_id, {"status": "locked", "elapsed_s": round(elapsed)}
            else:
                log(f"  ✓ {source_id}: guardados {last_done.get('saved')}, total en DB "
                    f"{last_done.get('total_db')}, rango {last_done.get('min_date')} -> "
                    f"{last_done.get('max_date')} ({elapsed:.0f}s)")
                return source_id, {
                    "status": "done", "elapsed_s": round(elapsed),
                    "seen": last_done.get("seen"), "saved": last_done.get("saved"),
                    "total_db": last_done.get("total_db"),
                    "min_date": last_done.get("min_date"), "max_date": last_done.get("max_date"),
                }
    except Exception as e:
        elapsed = time.time() - t0
        log(f"  ✗ {source_id}: error tras {elapsed:.0f}s -- {e}")
        return source_id, {"status": "error", "note": str(e), "elapsed_s": round(elapsed)}


def process_source(region, source_id):
    """Submitted to the worker pool per-source -- the needs_backfill live
    check happens here, right when a worker actually picks this item up,
    not at initial submission (submission happens for the whole queue at
    once; a source's lock/completeness state could genuinely change in
    the hours it takes the pool to get around to it)."""
    need, reason = needs_backfill(source_id)
    if not need:
        log(f"  ⏭ {source_id}: {reason}")
        return source_id, {"status": "skipped", "note": reason,
                            "checked_at": datetime.datetime.now().isoformat(timespec="seconds")}
    return run_one_backfill(region, source_id)


def main():
    progress = load_progress()
    queue = build_queue()
    log(f"=== Historical backfill campaign starting. {len(queue)} expansion sources total. ===")

    pending = [(region, sid) for region, sid in queue if progress.get(sid, {}).get("status") != "done"]
    log(f"{len(queue) - len(pending)} already marked done in a prior session, {len(pending)} left to check.")
    log(f"Rolling pool of {BATCH_SIZE} workers -- never more than {BATCH_SIZE} sources running "
        f"at once, but a freed worker picks up the next queued source immediately instead of "
        f"waiting for its original batch-mates to finish.")

    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
        futures = {pool.submit(process_source, region, sid): sid for region, sid in pending}
        for future in as_completed(futures):
            sid, outcome = future.result()
            outcome.setdefault("checked_at", datetime.datetime.now().isoformat(timespec="seconds"))
            progress[sid] = outcome
            save_progress(progress)

    done = sum(1 for v in progress.values() if v.get("status") == "done")
    skipped = sum(1 for v in progress.values() if v.get("status") == "skipped")
    errors = sum(1 for v in progress.values() if v.get("status") == "error")
    locked = sum(1 for v in progress.values() if v.get("status") == "locked")
    log(f"=== Campaign pass complete. done={done} skipped={skipped} errors={errors} "
        f"still-locked-elsewhere={locked} ===")
    if errors or locked:
        log("Some sources didn't finish cleanly -- re-run this script to retry just those "
            "(everything already 'done' is skipped automatically).")


if __name__ == "__main__":
    main()
