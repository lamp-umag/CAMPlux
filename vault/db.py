"""
vault — SQLite layer.

One database per source: data/yene_{source_id}.db
Each DB has:
  articles       — main table, url is the unique dedup key
  articles_fts   — FTS5 virtual table mirroring title + body_text
  scrape_log     — history of every scrape job (mode, range, result, status)
"""
import sqlite3
import datetime
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

ARCHIVE_STARTS = {
    "elpinguino":      "2009-01-01",
    "dialogosur":      "2010-05-20",
    "ovejeronoticias": "2015-07-17",
    "elmagallanico":   "2017-07-11",
    "laprensaaustral": "2020-01-30",
    "pepenoticias":    "2020-07-14",
    "zonazero":        "2021-04-26",
    "itvpatagonia":    "2023-07-01",
    "sosmagallanes":   "2025-05-01",
    "radiomagallanes": "2025-11-04",
    # Radio Polar: sitemap covers ~last 12 months only (no historical archive)
    "radiopolar":      "2025-05-01",
    # ── Nacional ──────────────────────────────────────────────────────────────
    "biobiochile":   "2009-05-01",
    "elmostrador":   "2026-05-01",
    "ciperchile":    "2007-01-01",
    "theclinic":     "2010-01-01",
    "elciudadano":   "2007-01-01",
    "cnnchile":      "2011-11-01",
    # ── Otras regiones ────────────────────────────────────────────────────────
    "ladiscusion":   "2015-01-01",
    # ── Internacional (WP REST API) ───────────────────────────────────────────
    "techcrunch":        "2005-06-01",
    "variety":           "2010-01-01",
    "rollingstone":      "2010-01-01",
    "hollywoodreporter": "2010-01-01",
    "technologyreview":  "2010-01-01",
    # ── Internacional (sitemap) ───────────────────────────────────────────────
    "clarin":            "2010-01-01",
    "theguardian":       "2026-05-27",
}

# ── schema ────────────────────────────────────────────────────────────────────

CREATE_ARTICLES = """
CREATE TABLE IF NOT EXISTS articles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    title       TEXT,
    url         TEXT    NOT NULL UNIQUE,
    body_text   TEXT,
    section     TEXT,
    image_url   TEXT,
    scraped_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_date   ON articles(date);
CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
"""

CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    title, body_text,
    content=articles,
    content_rowid=id,
    tokenize='unicode61'
);
"""

FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
    INSERT INTO articles_fts(rowid, title, body_text)
    VALUES (new.id, new.title, new.body_text);
END;
CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title, body_text)
    VALUES ('delete', old.id, old.title, old.body_text);
END;
CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title, body_text)
    VALUES ('delete', old.id, old.title, old.body_text);
    INSERT INTO articles_fts(rowid, title, body_text)
    VALUES (new.id, new.title, new.body_text);
END;
"""

CREATE_LOG = """
CREATE TABLE IF NOT EXISTS scrape_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT    NOT NULL,
    mode              TEXT,
    date_from         TEXT,
    date_to           TEXT,
    started_at        TEXT    NOT NULL,
    ended_at          TEXT,
    articles_seen     INTEGER DEFAULT 0,
    articles_inserted INTEGER DEFAULT 0,
    status            TEXT    DEFAULT 'running',
    note              TEXT
);
"""


# ── connection ────────────────────────────────────────────────────────────────

def db_path(source_id):
    return os.path.join(DATA_DIR, f"yene_{source_id}.db")


def db_exists(source_id):
    return os.path.exists(db_path(source_id))


def connect(source_id):
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(db_path(source_id))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def init_db(source_id):
    con = connect(source_id)
    con.executescript(CREATE_ARTICLES)
    con.executescript(CREATE_FTS)
    con.executescript(FTS_TRIGGERS)
    con.executescript(CREATE_LOG)
    # Migration: add image_url column to legacy DBs that pre-date the column
    cols = [r[1] for r in con.execute("PRAGMA table_info(articles)").fetchall()]
    if "image_url" not in cols:
        con.execute("ALTER TABLE articles ADD COLUMN image_url TEXT")
    # Migration: repair_checked_at tracks the body-text repair pass (2026-08-10)
    # -- NULL means "not attempted yet", set on every attempt (success or a
    # genuinely-short-article outcome) so repair makes monotonic progress
    # instead of re-selecting the same rows forever.
    if "repair_checked_at" not in cols:
        con.execute("ALTER TABLE articles ADD COLUMN repair_checked_at TEXT")
    # Migration: image_local_path (2026-08-10) -- NULL = not attempted,
    # '' = attempted but failed/no image, non-empty = downloaded successfully.
    # Distinguishing "failed" from "not tried" the same way repair_checked_at
    # does, so a backfill pass makes monotonic progress instead of retrying
    # the same permanently-broken URLs forever.
    if "image_local_path" not in cols:
        con.execute("ALTER TABLE articles ADD COLUMN image_local_path TEXT")
        con.execute("ALTER TABLE articles ADD COLUMN image_checked_at TEXT")
    con.commit()
    con.close()


# ── articles ──────────────────────────────────────────────────────────────────

def insert_articles(source_id, articles):
    """Bulk-insert, silently skips duplicates. Returns (inserted, skipped)."""
    if not articles:
        return 0, 0
    now = datetime.datetime.utcnow().isoformat()
    rows = [
        (a.get("source", source_id), a.get("date", ""), a.get("title", ""),
         a.get("url", ""), a.get("body_text", ""), a.get("section", ""),
         a.get("image_url", ""), now)
        for a in articles if a.get("url")
    ]
    con = connect(source_id)
    before = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    con.executemany(
        "INSERT OR IGNORE INTO articles "
        "(source, date, title, url, body_text, section, image_url, scraped_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    after = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    con.close()
    inserted = after - before
    return inserted, len(rows) - inserted


# ── body-text repair (added 2026-08-10, see scrapers/elpinguino.py) ─────────
# Re-scraping a date range that already has data does nothing --
# insert_articles() is INSERT OR IGNORE, so an existing (bad) row's URL
# conflict just gets silently skipped. Repairing existing rows needs an
# actual UPDATE path, which is what these do.

MIN_PLAUSIBLE_BODY_CHARS = 150


def count_unrepaired_short(source_id):
    con = connect(source_id)
    n = con.execute(
        "SELECT COUNT(*) FROM articles "
        "WHERE LENGTH(body_text) < ? AND repair_checked_at IS NULL",
        (MIN_PLAUSIBLE_BODY_CHARS,),
    ).fetchone()[0]
    con.close()
    return n


def get_unrepaired_short_articles(source_id, limit=200):
    con = connect(source_id)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, url, date, body_text FROM articles "
        "WHERE LENGTH(body_text) < ? AND repair_checked_at IS NULL "
        "ORDER BY date DESC LIMIT ?",
        (MIN_PLAUSIBLE_BODY_CHARS, limit),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def apply_repair_result(source_id, article_id, new_body_text, new_image_url):
    """Always stamps repair_checked_at (attempted), and only overwrites
    body_text/image_url if the new fetch actually produced something
    longer -- a genuinely short article (real content, just brief) keeps
    its real text rather than being blanked by a fetch that came back
    short again for a legitimate reason."""
    con = connect(source_id)
    now = datetime.datetime.now(datetime.UTC).isoformat()
    row = con.execute("SELECT body_text FROM articles WHERE id = ?", (article_id,)).fetchone()
    old_len = len(row[0] or "") if row else 0
    improved = new_body_text and len(new_body_text) > old_len
    if improved:
        con.execute(
            "UPDATE articles SET body_text = ?, image_url = COALESCE(NULLIF(?, ''), image_url), "
            "repair_checked_at = ? WHERE id = ?",
            (new_body_text, new_image_url or "", now, article_id),
        )
    else:
        con.execute(
            "UPDATE articles SET repair_checked_at = ? WHERE id = ?",
            (now, article_id),
        )
    con.commit()
    con.close()
    return improved


# ── image file backfill (added 2026-08-10) ───────────────────────────────────
# image_url alone rots (external links die); this downloads the actual bytes.
# See vault/images.py for the fetch itself.

def count_missing_image_files(source_id):
    con = connect(source_id)
    n = con.execute(
        "SELECT COUNT(*) FROM articles WHERE image_url != '' AND image_url IS NOT NULL "
        "AND image_checked_at IS NULL"
    ).fetchone()[0]
    con.close()
    return n


def get_articles_missing_image_file(source_id, limit=200):
    con = connect(source_id)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, url, image_url FROM articles "
        "WHERE image_url != '' AND image_url IS NOT NULL AND image_checked_at IS NULL "
        "ORDER BY date DESC LIMIT ?",
        (limit,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def set_image_result(source_id, article_id, local_path):
    """local_path: relative path string on success, None/'' on failure (still
    stamps image_checked_at either way, so a permanently-dead image URL
    doesn't get retried forever)."""
    con = connect(source_id)
    now = datetime.datetime.now(datetime.UTC).isoformat()
    con.execute(
        "UPDATE articles SET image_local_path = ?, image_checked_at = ? WHERE id = ?",
        (local_path or "", now, article_id),
    )
    con.commit()
    con.close()


# ── scrape log ────────────────────────────────────────────────────────────────

def log_start(source_id, mode, date_from, date_to):
    """Create a log entry for a new scrape job. Returns the job id."""
    init_db(source_id)
    con = connect(source_id)
    cur = con.execute(
        "INSERT INTO scrape_log (source, mode, date_from, date_to, started_at, status) "
        "VALUES (?,?,?,?,?,?)",
        (source_id, mode, date_from, date_to,
         datetime.datetime.utcnow().isoformat(), "running"),
    )
    job_id = cur.lastrowid
    con.commit()
    con.close()
    return job_id


def log_end(job_id, source_id, status, seen, inserted, note=""):
    """Finalise a log entry."""
    con = connect(source_id)
    con.execute(
        "UPDATE scrape_log SET ended_at=?, status=?, "
        "articles_seen=?, articles_inserted=?, note=? WHERE id=?",
        (datetime.datetime.utcnow().isoformat(), status, seen, inserted, note, job_id),
    )
    con.commit()
    con.close()


def get_scrape_history(source_id, limit=15):
    if not db_exists(source_id):
        return []
    con = connect(source_id)
    rows = con.execute(
        "SELECT id, mode, date_from, date_to, started_at, ended_at, "
        "articles_seen, articles_inserted, status, note "
        "FROM scrape_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ── coverage & status ─────────────────────────────────────────────────────────

def get_coverage_by_year(source_id):
    """Returns {year_str: count} for all years present in articles."""
    if not db_exists(source_id):
        return {}
    con = connect(source_id)
    rows = con.execute(
        "SELECT substr(date,1,4) yr, COUNT(*) n FROM articles GROUP BY yr ORDER BY yr"
    ).fetchall()
    con.close()
    return {r["yr"]: r["n"] for r in rows}


def get_status(source_id):
    if not db_exists(source_id):
        return {
            "exists": False, "count": 0,
            "min_date": None, "max_date": None,
            "last_scraped": None, "size_mb": 0,
            "archive_start": ARCHIVE_STARTS.get(source_id),
            "coverage": {},
        }
    con = connect(source_id)
    row = con.execute(
        "SELECT COUNT(*) n, MIN(date) mn, MAX(date) mx, MAX(scraped_at) ls FROM articles"
    ).fetchone()
    coverage_rows = con.execute(
        "SELECT substr(date,1,4) yr, COUNT(*) n FROM articles GROUP BY yr ORDER BY yr"
    ).fetchall()
    con.close()
    size = os.path.getsize(db_path(source_id)) / 1_048_576
    return {
        "exists":        True,
        "count":         row["n"],
        "min_date":      row["mn"],
        "max_date":      row["mx"],
        "last_scraped":  row["ls"],
        "size_mb":       round(size, 1),
        "archive_start": ARCHIVE_STARTS.get(source_id),
        "coverage":      {r["yr"]: r["n"] for r in coverage_rows},
    }


def get_update_start(source_id):
    status = get_status(source_id)
    if not status["exists"] or not status["max_date"]:
        return ARCHIVE_STARTS.get(source_id, "2010-01-01")
    dt = datetime.date.fromisoformat(status["max_date"])
    return (dt - datetime.timedelta(days=2)).isoformat()
