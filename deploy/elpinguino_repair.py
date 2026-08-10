#!/usr/bin/env python3
"""
Bounded, resumable driver for /repair?source=elpinguino.

Calls /repair in batches (each batch is itself bounded server-side, and only
holds the per-source lock for that one batch -- see scheduler_db.py) until
either nothing's left, a hard wall-clock ceiling is hit, or too many
consecutive empty/locked batches suggest something's stuck. Resumable by
construction: progress lives in the DB (repair_checked_at), not in this
script's state, so killing and re-running it just continues where it left
off -- no separate checkpoint file needed.

Usage:
    python3 elpinguino_repair.py [--minutes 45] [--batch-size 300]

Deliberately NOT a single unbounded "fix everything" run -- per-run time
ceiling is the point, not a nice-to-have.
"""
import argparse
import datetime
import json
import time
import urllib.request

VAULT_BASE = "http://127.0.0.1:5001"
BATCH_TIMEOUT_S = 900  # one batch (default 300 articles at ~5 workers) should
                        # take a few minutes; this is a generous ceiling per
                        # single /repair call, not the whole session


def sse_stream(url, timeout=BATCH_TIMEOUT_S):
    """Yields parsed JSON events from an SSE endpoint."""
    with urllib.request.urlopen(url, timeout=timeout) as r:
        for raw_line in r:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            try:
                yield json.loads(line[len("data: "):])
            except json.JSONDecodeError:
                continue


def run_batch(source_id, limit):
    url = f"{VAULT_BASE}/repair?source={source_id}&limit={limit}"
    done_event = None
    for event in sse_stream(url):
        if event.get("type") == "done":
            done_event = event
    return done_event


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="elpinguino")
    ap.add_argument("--minutes", type=float, default=45,
                     help="hard wall-clock ceiling for this whole session")
    ap.add_argument("--batch-size", type=int, default=300)
    args = ap.parse_args()

    deadline = time.monotonic() + args.minutes * 60
    session_start = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"=== elpinguino_repair.py session starting {session_start} "
          f"(ceiling {args.minutes} min, batch size {args.batch_size}) ===", flush=True)

    total_checked, total_improved = 0, 0
    consecutive_empty = 0
    batch_n = 0

    while time.monotonic() < deadline:
        batch_n += 1
        remaining_time = deadline - time.monotonic()
        if remaining_time < 30:
            print("Less than 30s left in this session's ceiling, stopping before starting another batch.", flush=True)
            break

        t0 = time.time()
        try:
            result = run_batch(args.source, args.batch_size)
        except Exception as e:
            print(f"batch {batch_n}: ERROR calling /repair: {e}", flush=True)
            time.sleep(10)
            consecutive_empty += 1
            if consecutive_empty >= 5:
                print("5 consecutive errors, stopping this session.", flush=True)
                break
            continue

        if result is None:
            print(f"batch {batch_n}: no 'done' event received (connection issue?)", flush=True)
            consecutive_empty += 1
        else:
            checked = result.get("checked", 0)
            improved = result.get("improved", 0)
            remaining = result.get("remaining")
            elapsed = time.time() - t0
            total_checked += checked
            total_improved += improved
            print(f"batch {batch_n}: checked={checked} improved={improved} "
                  f"remaining={remaining} ({elapsed:.0f}s)", flush=True)

            if checked == 0:
                consecutive_empty += 1
            else:
                consecutive_empty = 0

            if remaining == 0:
                print("Nothing left to repair -- done!", flush=True)
                break

        if consecutive_empty >= 5:
            print("5 consecutive empty/locked batches in a row -- something's "
                  "probably stuck (another job holding the lock?). Stopping "
                  "this session rather than spinning.", flush=True)
            break

        time.sleep(2)  # brief pause between batches, polite + lets other jobs interleave

    session_end = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"=== session ending {session_end}: {batch_n} batches, "
          f"{total_checked} articles checked, {total_improved} improved ===", flush=True)


if __name__ == "__main__":
    main()
