#!/usr/bin/env python3
"""
Overnight campaign runner, 2026-08-10.

Sequences a fixed list of bounded tasks -- never runs everything at once,
never runs any single task unboundedly. Each task has its own hard
wall-clock ceiling; if it's not done when the ceiling hits, it stops
cleanly (mid-batch, via the same bounded-batch pattern as
elpinguino_repair.py) and the campaign moves to the next task. Progress
within each task is checkpointed in Vault's own DB (repair_checked_at,
image_checked_at, or the archive itself), so re-running this script, or any
individual task, is always safe and picks up where it left off.

Logs everything to one file so the whole night's work is reviewable in one
place. Run detached (nohup ... &, already how this is launched).
"""
import datetime
import json
import time
import urllib.request
import urllib.parse

VAULT_BASE = "http://127.0.0.1:5001"


def sse_stream(url, timeout=900):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        for raw_line in r:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            try:
                yield json.loads(line[len("data: "):])
            except json.JSONDecodeError:
                continue


def get_json(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ── bounded task runners ──────────────────────────────────────────────────

def run_repair_session(source_id, minutes, batch_size=300):
    """Repeated /repair batches until nothing's left or the ceiling hits."""
    deadline = time.monotonic() + minutes * 60
    total_checked, total_improved = 0, 0
    consecutive_empty = 0
    while time.monotonic() < deadline:
        if deadline - time.monotonic() < 20:
            break
        try:
            url = f"{VAULT_BASE}/repair?source={source_id}&limit={batch_size}"
            done = None
            for event in sse_stream(url):
                if event.get("type") == "done":
                    done = event
        except Exception as e:
            log(f"  repair batch error: {e}")
            time.sleep(10)
            consecutive_empty += 1
            if consecutive_empty >= 5:
                break
            continue

        if not done:
            consecutive_empty += 1
        else:
            checked, improved = done.get("checked", 0), done.get("improved", 0)
            remaining = done.get("remaining")
            total_checked += checked
            total_improved += improved
            log(f"  repair batch: checked={checked} improved={improved} remaining={remaining}")
            consecutive_empty = 0 if checked else consecutive_empty + 1
            if remaining == 0:
                log("  nothing left to repair")
                break
        if consecutive_empty >= 5:
            log("  5 empty/locked batches in a row, stopping this task")
            break
        time.sleep(2)
    log(f"repair[{source_id}] session total: checked={total_checked} improved={total_improved}")


def run_image_session(source_id, minutes, batch_size=100):
    """Repeated /images/backfill batches until nothing's left or ceiling hits."""
    deadline = time.monotonic() + minutes * 60
    total_checked, total_downloaded = 0, 0
    consecutive_empty = 0
    while time.monotonic() < deadline:
        if deadline - time.monotonic() < 20:
            break
        try:
            url = f"{VAULT_BASE}/images/backfill?source={source_id}&limit={batch_size}"
            done = None
            for event in sse_stream(url):
                if event.get("type") == "done":
                    done = event
        except Exception as e:
            log(f"  image batch error: {e}")
            time.sleep(10)
            consecutive_empty += 1
            if consecutive_empty >= 5:
                break
            continue

        if not done:
            consecutive_empty += 1
        else:
            checked, downloaded = done.get("checked", 0), done.get("downloaded", 0)
            remaining = done.get("remaining")
            total_checked += checked
            total_downloaded += downloaded
            log(f"  image batch: checked={checked} downloaded={downloaded} remaining={remaining}")
            consecutive_empty = 0 if checked else consecutive_empty + 1
            if remaining == 0:
                log("  nothing left to download")
                break
        if consecutive_empty >= 5:
            log("  5 empty/locked batches in a row, stopping this task")
            break
        time.sleep(1)
    log(f"images[{source_id}] session total: checked={total_checked} downloaded={total_downloaded}")


def run_archive_session(source_id, mode, minutes):
    """A single bounded /archive call (mode=full for an empty source). Vault's
    own SSE stream doesn't chunk itself, so 'bounded' here means: give up
    waiting past `minutes` and move on -- whatever got saved before that
    stays saved (batched inserts, same as everywhere else in this app)."""
    deadline_s = minutes * 60
    url = f"{VAULT_BASE}/archive?source={source_id}&mode={mode}"
    last_progress_count = 0
    try:
        start = time.monotonic()
        for event in sse_stream(url, timeout=deadline_s + 30):
            if time.monotonic() - start > deadline_s:
                log(f"  {source_id}: time budget ({minutes}min) reached mid-scrape, "
                    f"moving on (progress so far is saved)")
                break
            if event.get("type") == "progress":
                last_progress_count = event.get("total", last_progress_count)
            elif event.get("type") == "done":
                log(f"  {source_id}: done -- seen={event.get('seen')} saved={event.get('saved')}")
            elif event.get("type") == "log" and event.get("level") in ("error", "warn"):
                log(f"  {source_id}: {event.get('msg')}")
    except Exception as e:
        log(f"  {source_id}: error during archive session: {e} "
            f"(progress so far, {last_progress_count} articles, is still saved)")


# ── campaign ──────────────────────────────────────────────────────────────

TASKS = [
    ("repair",  "elpinguino",       90),
    ("images",  "laprensaaustral",  60),
    ("archive_full", "ciperchile",   30),
    ("archive_full", "elciudadano",  30),
    ("archive_full", "ladiscusion",  30),
    ("archive_full", "theclinic",    30),
    ("archive_full", "biobiochile",  30),
    ("archive_full", "cnnchile",     30),
    ("archive_full", "elmostrador",  15),
    ("repair",  "elpinguino",       60),   # round 2, more time now the site's had a break
    ("images",  "elpinguino",       30),   # repaired articles now have real image_urls too
    ("images",  "laprensaaustral",  30),
]


def main():
    campaign_start = datetime.datetime.now().isoformat()
    log(f"=== overnight_campaign.py starting, {len(TASKS)} tasks queued ===")

    for i, (kind, source_id, minutes) in enumerate(TASKS, 1):
        log(f"--- task {i}/{len(TASKS)}: {kind} {source_id} (budget {minutes}min) ---")
        t0 = time.monotonic()
        try:
            if kind == "repair":
                run_repair_session(source_id, minutes)
            elif kind == "images":
                run_image_session(source_id, minutes)
            elif kind == "archive_full":
                run_archive_session(source_id, "full", minutes)
        except Exception as e:
            log(f"  UNEXPECTED ERROR in task {i} ({kind} {source_id}): {e} -- moving on")
        elapsed = (time.monotonic() - t0) / 60
        log(f"--- task {i} finished after {elapsed:.1f} min ---")

    log(f"=== campaign done, started {campaign_start}, ended {datetime.datetime.now().isoformat()} ===")


if __name__ == "__main__":
    main()
