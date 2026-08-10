#!/usr/bin/env python3
"""
Nightly incremental update for every source Vault already has data for.

Hits Vault directly on its loopback-only port (127.0.0.1:5001, see
docker-compose.yml) -- this script runs on the host via a systemd timer, not
through Caddy/Basic Auth, same trust model as any other localhost-bound
service on this machine.

IMPORTANT -- why this skips sources with no existing data:
Vault's own update-start logic (db.get_update_start) falls back to each
source's full ARCHIVE_STARTS date (sometimes 2007+) when there's no data
yet, meaning `mode=update` on an empty source triggers a FULL HISTORICAL
BACKFILL, not a small incremental update. Running that unattended, for every
configured source, every night, the first time this timer fires would mean
hammering ~18 different news sites for years of history all at once --
not something to do unsupervised. So: sources with existing data get a
small `mode=update` (genuinely incremental, that's what the endpoint is
for). Sources with none are skipped and logged -- kick off their first,
one-time backfill yourself, deliberately, e.g.:

    curl "http://127.0.0.1:5001/archive?source=<id>&mode=full"

one at a time, when you're ready to (a) actually wait for it and (b) not
do all 18 at once. After that first run, this nightly job picks it up
automatically like any other source.

Also respects the per-source "nightly" toggle in the dashboard
(vault/schedule/state) -- a source with data but toggled off is skipped too.

Locking against other jobs (a manual repair pass, a one-off scheduled run)
is handled server-side, inside /archive itself (see scheduler_db.py's
source_locks) -- this script doesn't need its own lock check, it just needs
to read a "locked" outcome as a skip, not a failure (see run_update()).
"""
import datetime
import json
import sys
import urllib.request

VAULT_BASE = "http://127.0.0.1:5001"
TIMEOUT_S = 1800  # a source's incremental update should be quick, but give
                   # real headroom for a slow night on any one site


def get_json(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(url, body, timeout=30):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def run_update(source_id):
    """Blocks until Vault's SSE stream for this source finishes; returns the
    final 'done' event's dict, or None if the stream ended without one."""
    url = f"{VAULT_BASE}/archive?source={source_id}&mode=update"
    last_done = None
    with urllib.request.urlopen(url, timeout=TIMEOUT_S) as r:
        for raw_line in r:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            try:
                event = json.loads(line[len("data: "):])
            except json.JSONDecodeError:
                continue
            if event.get("type") == "done":
                last_done = event
    return last_done


def main():
    started = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"=== nightly_archive.py starting {started} ===")

    status = get_json(f"{VAULT_BASE}/status")
    schedule_state = get_json(f"{VAULT_BASE}/schedule/state")
    nightly_enabled = schedule_state.get("nightly_enabled", {})

    no_data = sorted(s for s, info in status.items() if not info.get("exists"))
    disabled = sorted(s for s in status if not nightly_enabled.get(s, True))
    to_update = sorted(
        s for s, info in status.items()
        if info.get("exists") and nightly_enabled.get(s, True)
    )

    if no_data:
        print(f"Skipping {len(no_data)} source(s) with no archive yet "
              f"(needs a one-time manual backfill first): {', '.join(no_data)}")
    if disabled:
        print(f"Skipping {len(disabled)} source(s) with nightly updates turned off "
              f"in the dashboard: {', '.join(disabled)}")

    ok, failed, locked_out = [], [], []
    detail = {}
    for source_id in to_update:
        print(f"--- updating {source_id} ---")
        try:
            result = run_update(source_id)
        except Exception as e:
            print(f"  ERROR: {e}")
            failed.append(source_id)
            detail[source_id] = {"status": "error", "note": str(e)}
            continue

        if result is None:
            print("  WARNING: stream ended with no 'done' event")
            failed.append(source_id)
            detail[source_id] = {"status": "error", "note": "no 'done' event"}
            continue

        if result.get("job_status") == "locked":
            print(f"  locked by another job right now, skipping tonight")
            locked_out.append(source_id)
            detail[source_id] = {"status": "locked"}
            continue

        print(f"  saved={result.get('saved')} seen={result.get('seen')} "
              f"total_db={result.get('total_db')} "
              f"range={result.get('min_date')}..{result.get('max_date')}")
        ok.append(source_id)
        detail[source_id] = {
            "status": "done", "saved": result.get("saved"), "seen": result.get("seen"),
            "total_db": result.get("total_db"),
        }

    finished = datetime.datetime.now(datetime.UTC).isoformat()
    print(f"=== done: {len(ok)} updated, {len(failed)} failed, "
          f"{len(no_data)} skipped (no archive), {len(disabled)} skipped (disabled), "
          f"{len(locked_out)} skipped (locked by another job) ===")

    try:
        post_json(f"{VAULT_BASE}/schedule/nightly_run", {
            "started_at": started, "finished_at": finished,
            "updated": len(ok), "failed": len(failed),
            "skipped_no_data": len(no_data), "skipped_disabled": len(disabled),
            "detail": detail,
        })
    except Exception as e:
        # Don't fail the whole run over a logging call -- the actual scrapes
        # already happened and are safe in each source's own DB either way.
        print(f"WARNING: failed to record run summary in dashboard: {e}")

    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
