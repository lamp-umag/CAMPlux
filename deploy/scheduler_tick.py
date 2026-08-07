#!/usr/bin/env python3
"""
Runs frequently (every ~10 min, via camplux-scheduler-tick.timer) and
executes any one-off scheduled run whose time has come (scheduled from the
Vault dashboard's "Programar" button -> POST /schedule/once).

Separate from nightly_archive.py (which handles the recurring nightly pass
for every source with existing data) -- this one only touches whatever a
human deliberately scheduled for a specific date/time, including a
first-ever backfill for a source that has no data yet (that's the intended
way to kick one off without babysitting a terminal: schedule it via the
dashboard for a few minutes from now, or overnight).
"""
import datetime
import json
import urllib.parse
import urllib.request

VAULT_BASE = "http://127.0.0.1:5001"
TIMEOUT_S = 21600  # a scheduled full backfill can legitimately take hours


def get_json(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post(url, timeout=30):
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def run_archive(source_id, mode, date_from=None, date_to=None):
    params = {"source": source_id, "mode": mode}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    url = f"{VAULT_BASE}/archive?{urllib.parse.urlencode(params)}"

    last_done, last_error = None, None
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
            elif event.get("type") == "log" and event.get("level") == "error":
                last_error = event.get("msg")
    return last_done, last_error


def main():
    # run_at values come from the dashboard's <input type=datetime-local>,
    # which submits a naive "local wall-clock time" string with no timezone
    # -- comparing that against a UTC "now" (as an earlier version of this
    # script did, via string comparison) is wrong by this server's UTC
    # offset (3 hours on this box), silently running jobs early or late.
    # Use naive local time throughout so it matches what the browser sent.
    now = datetime.datetime.now().isoformat()
    due = get_json(f"{VAULT_BASE}/schedule/state")["pending"]
    due = [r for r in due if r["run_at"] <= now]

    if not due:
        return  # quiet on the common case -- this runs every ~10 minutes

    print(f"=== scheduler_tick.py {now}: {len(due)} due job(s) ===")
    for job in due:
        rid, source_id, mode = job["id"], job["source_id"], job["mode"]
        print(f"--- running scheduled job #{rid}: {source_id} ({mode}) ---")
        try:
            result, error = run_archive(source_id, mode, job.get("date_from"), job.get("date_to"))
        except Exception as e:
            print(f"  ERROR: {e}")
            _mark(rid, "error", str(e))
            continue

        if result is None:
            note = error or "stream ended with no 'done' event"
            print(f"  WARNING: {note}")
            _mark(rid, "error", note)
            continue

        note = (f"saved={result.get('saved')} seen={result.get('seen')} "
                f"total_db={result.get('total_db')}")
        print(f"  {note}")
        _mark(rid, "done", note)


def _mark(run_id, status, note):
    # POST /schedule/mark/<id> -- a real Vault endpoint, not direct DB
    # access: Vault's actual scheduler DB lives inside a Docker named
    # volume, not at a host filesystem path this script could import its
    # way into.
    params = urllib.parse.urlencode({"status": status, "note": note or ""})
    try:
        post(f"{VAULT_BASE}/schedule/mark/{run_id}?{params}")
    except Exception as e:
        print(f"  WARNING: failed to record outcome for #{run_id}: {e}")


if __name__ == "__main__":
    main()
