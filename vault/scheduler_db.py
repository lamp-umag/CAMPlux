"""
vault — scheduling layer.

Separate from db.py's per-source article DBs (data/yene_{source}.db) --
this is control/meta state, not archive data, so it lives in its own file:
data/_scheduler.db.

Three concerns:
  - nightly_enabled: per-source on/off switch for the recurring nightly
    update pass (deploy/nightly_archive.py checks this before running).
  - scheduled_runs: one-off future runs ("scrape X at this date/time"),
    picked up and executed by deploy/scheduler_tick.py.
  - nightly_runs: a record of each nightly pass actually happening (or not)
    -- "what's supposed to happen when, and did it" is the whole point of
    a scheduling dashboard; a schedule nobody can see the outcome of isn't
    actually answering that.
"""
import sqlite3
import datetime
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "_scheduler.db")


def _connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db():
    con = _connect()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS source_config (
            source_id TEXT PRIMARY KEY,
            nightly_enabled INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS scheduled_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            run_at TEXT NOT NULL,
            date_from TEXT,
            date_to TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            executed_at TEXT,
            result_note TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_scheduled_runs_status
            ON scheduled_runs(status, run_at);
        CREATE TABLE IF NOT EXISTS nightly_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            updated_count INTEGER NOT NULL,
            failed_count INTEGER NOT NULL,
            skipped_no_data_count INTEGER NOT NULL,
            skipped_disabled_count INTEGER NOT NULL,
            detail_json TEXT
        );
    """)
    con.commit()
    con.close()


def now_iso():
    """UTC, for audit timestamps (created_at/executed_at) -- NOT for
    comparing against run_at, which is naive local time from the
    dashboard's <input type=datetime-local>. Use now_local_iso() for that."""
    return datetime.datetime.now(datetime.UTC).isoformat()


def now_local_iso():
    return datetime.datetime.now().isoformat()


# ── nightly on/off ──────────────────────────────────────────────────────────

def is_nightly_enabled(source_id):
    con = _connect()
    row = con.execute(
        "SELECT nightly_enabled FROM source_config WHERE source_id = ?",
        (source_id,),
    ).fetchone()
    con.close()
    return True if row is None else bool(row["nightly_enabled"])


def set_nightly_enabled(source_id, enabled):
    con = _connect()
    con.execute(
        """INSERT INTO source_config (source_id, nightly_enabled) VALUES (?, ?)
           ON CONFLICT(source_id) DO UPDATE SET nightly_enabled = excluded.nightly_enabled""",
        (source_id, int(bool(enabled))),
    )
    con.commit()
    con.close()


def all_nightly_states(source_ids):
    con = _connect()
    rows = con.execute("SELECT source_id, nightly_enabled FROM source_config").fetchall()
    con.close()
    overrides = {r["source_id"]: bool(r["nightly_enabled"]) for r in rows}
    return {sid: overrides.get(sid, True) for sid in source_ids}


# ── one-off scheduled runs ───────────────────────────────────────────────────

def add_scheduled_run(source_id, mode, run_at, date_from=None, date_to=None):
    con = _connect()
    cur = con.execute(
        """INSERT INTO scheduled_runs
           (source_id, mode, run_at, date_from, date_to, status, created_at)
           VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
        (source_id, mode, run_at, date_from, date_to, now_iso()),
    )
    con.commit()
    new_id = cur.lastrowid
    con.close()
    return new_id


def list_scheduled_runs(limit=100):
    con = _connect()
    rows = con.execute(
        "SELECT * FROM scheduled_runs ORDER BY run_at DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_due_scheduled_runs():
    con = _connect()
    rows = con.execute(
        "SELECT * FROM scheduled_runs WHERE status = 'pending' AND run_at <= ? ORDER BY run_at",
        (now_local_iso(),),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def mark_scheduled_run(run_id, status, note=None):
    con = _connect()
    con.execute(
        "UPDATE scheduled_runs SET status = ?, executed_at = ?, result_note = ? WHERE id = ?",
        (status, now_iso(), note, run_id),
    )
    con.commit()
    con.close()


def cancel_scheduled_run(run_id):
    con = _connect()
    cur = con.execute(
        "UPDATE scheduled_runs SET status = 'cancelled', executed_at = ? WHERE id = ? AND status = 'pending'",
        (now_iso(), run_id),
    )
    con.commit()
    changed = cur.rowcount > 0
    con.close()
    return changed


# ── nightly run history (the "did it actually happen" record) ──────────────

def log_nightly_run(started_at, finished_at, updated, failed, skipped_no_data,
                     skipped_disabled, detail):
    con = _connect()
    con.execute(
        """INSERT INTO nightly_runs
           (started_at, finished_at, updated_count, failed_count,
            skipped_no_data_count, skipped_disabled_count, detail_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (started_at, finished_at, updated, failed, skipped_no_data,
         skipped_disabled, json.dumps(detail, ensure_ascii=False)),
    )
    con.commit()
    con.close()


def list_nightly_runs(limit=14):
    con = _connect()
    rows = con.execute(
        "SELECT * FROM nightly_runs ORDER BY started_at DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["detail"] = json.loads(d.pop("detail_json") or "{}")
        except json.JSONDecodeError:
            d["detail"] = {}
        out.append(d)
    return out
