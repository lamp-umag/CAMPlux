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
    # ── Aysén (national expansion, see deploy/expansion/) ─────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "diariodeaysen":     "2026-03-25",
    "diarioaysen":       "2022-05-13",
    "canalsurpatagonia": "2024-01-02",
    "radiosantamaria":   "2018-06-28",
    "rln":               "2018-01-01",
    # ── Arica y Parinacota (national expansion) ────────────────────────────────
    "aricahoy":              "2012-11-22",
    "aricaldia":             "2014-10-09",
    "elmorrodearica":        "2020-10-06",
    "cappissimamultimedial": "2023-07-21",
    # ── Atacama (national expansion) ────────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "atacamanoticias":  "2019-10-01",
    "chanarcillo":      "2015-03-13",
    "tierramarillano":  "2017-01-13",
    "hvaradio":         "2019-04-01",
    "atacamaenlinea":   "2012-02-20",
    "madero":           "2022-06-01",
    # ── Tarapacá (national expansion) ───────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "diariolongino": "2021-11-08",
    "iquiquetv":     "2018-09-13",
    "iquiquealdia":  "2024-01-01",
    "radiopaulina":  "2009-02-02",
    "rtccormudesi":  "2026-07-13",
    # ── Los Ríos (national expansion) ───────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed. (noticiaslosrios:
    # one single post has a data-entry-typo year "0026"; used the site's
    # real oldest post instead, see the scraper's own docstring.)
    "radioaustralvaldivia": "2020-09-18",
    "losriosaldia":         "2013-06-25",
    "periodicolosrios":     "2018-08-08",
    "noticiaslosrios":      "2014-02-21",
    "rioenlinea":           "2018-08-01",
    "diarioelranco":        "2009-07-08",
    # ── Ñuble (national expansion) ──────────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "nubleonline":      "2023-04-18",
    "nubleactual":      "2023-10-30",
    "lafontana":        "2020-04-16",
    "quirihuenoticias": "2021-06-19",
    "radiocontacto":    "2021-12-07",
    "radionuble":       "2024-12-02",
    # ── Antofagasta (national expansion) ────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "diarioantofagasta": "2011-02-07",
    "regionalista":      "2018-03-05",
    "radionuevomundo":   "2017-01-03",
    # ── Coquimbo (national expansion) ───────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed. (laserenaonline:
    # one single post has a data-entry-typo year "0027"; used the site's real
    # oldest post instead, see the scraper's own docstring.)
    "ovallehoy":      "2014-07-19",
    "laserenaonline": "2015-08-10",
    "elcoquimbano":   "2020-08-20",
    "elillapelino":   "2020-11-02",
    "diariochoapa":   "2021-07-17",
    "radioriquelme":  "2019-01-29",
    # ── Los Lagos (national expansion) ──────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "diarioloslagos":    "2025-10-06",
    "chiloenews":        "2021-06-01",
    "laopiniondechiloe": "2015-02-08",
    "diariopuertovaras": "2017-10-18",
    "radiofrutillarfm":  "2023-07-20",
    # ── O'Higgins (national expansion) ──────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed. (diarioelmarino:
    # oldest indexed posts are a real digitized 1907 historical archive, not
    # a data-entry typo -- see the scraper's own docstring.)
    "elrancaguino":     "2009-10-01",
    "diarioelpulso":    "2019-09-01",
    "radiomachali":     "2026-03-31",
    "diariorancagua":   "2013-10-31",
    "hdn":              "2015-09-05",
    "tribunacolchagua": "2023-01-04",
    "diarioelmarino":   "1907-08-18",
    "pichilemutv":      "2008-04-29",
    "radiosantacruz":   "2021-10-08",
    # ── Araucanía (national expansion) ──────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "araucanianoticias":    "2011-01-28",
    "elperiodico":          "2025-07-09",
    "malleconoticias":      "2026-02-23",
    "angolnoticiasnew":     "2023-12-29",
    "lasnoticiasdemalleco": "2022-07-20",
    "elespejodemalleco":    "2019-11-25",
    "malleco7":             "2019-05-05",
    "villarricaldia":       "2023-05-10",
    # ── Maule (national expansion) ──────────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed. (cauquenesnet:
    # oldest indexed posts are a real digitized political-history archive
    # back to 2000, not a data-entry typo -- see the scraper's own
    # docstring.)
    "diariotalca":          "2020-12-03",
    "elmauleinforma":       "2020-09-07",
    "radiochilenadelmaule": "2021-03-11",
    "diarioelcentro":       "2022-02-25",
    "cronicanoticias":      "2024-01-03",
    "diariolinares":        "2020-12-03",
    "diariocauquenes":      "2020-12-03",
    "linaresenlinea":       "2016-09-19",
    "cauquenesnet":         "2000-03-12",
    # ── Biobío (national expansion) ─────────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "bionoticias":      "2014-06-01",
    "elcontraste":      "2019-03-10",
    "diarioprovincial": "2020-06-03",
    "araucovision":     "2025-03-05",
    # ── Valparaíso (national expansion) ─────────────────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "observador":     "2016-10-20",
    "g5noticias":     "2020-01-08",
    "diariolaquinta": "2018-03-08",
    "epicentrochile": "2012-07-18",
    "elaconcagua":    "2016-01-04",
    "elproa":         "2021-01-01",
    # ── Región Metropolitana (national expansion) ───────────────────────────
    # dates below = each site's own oldest-indexed WP post, confirmed live
    # 2026-08-22 via ?orderby=date&order=asc -- not guessed.
    "elcomunicador":       "2025-01-02",
    "diarioellabrador":    "2025-03-07",
    "portaldemelipilla":   "2017-01-09",
    "puentealtoaldia":     "2024-04-10",
    "puentealtonline":     "2024-06-24",
    "portalpuentealto":    "2002-09-04",
    "redhoy":              "2025-01-01",
    "lavozdemaipu":        "2009-08-05",
    "labatalla":           "2010-04-21",
    "noticiasdelsol":      "2023-02-08",
    "delh":                "2019-09-03",
    "portalmetropolitano": "2022-09-05",
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
    author      TEXT,
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
    # Migration: author (2026-08-11) -- most WP sites expose the real byline
    # via a structured user field the scraper never requested; NULL = not
    # backfilled yet, '' = backfilled but the site has no author for this row.
    if "author" not in cols:
        con.execute("ALTER TABLE articles ADD COLUMN author TEXT")
    # Migration: date indexes (2026-08-21) -- get_status()'s MIN/MAX(date) and
    # per-year GROUP BY substr(date,1,4) were doing a full table scan on every
    # call, which on the larger sources (elpinguino: ~192k rows) made /status
    # take 30-80s and blew nightly_archive.py's 30s request timeout every
    # night. Confirmed live before fixing, not guessed.
    con.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_articles_year ON articles(substr(date,1,4))")
    con.execute("CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at)")
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
         a.get("image_url", ""), a.get("author", ""), now)
        for a in articles if a.get("url")
    ]
    con = connect(source_id)
    before = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    con.executemany(
        "INSERT OR IGNORE INTO articles "
        "(source, date, title, url, body_text, section, image_url, author, scraped_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
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


def count_unrepaired_short(source_id, section=None):
    con = connect(source_id)
    if section:
        n = con.execute(
            "SELECT COUNT(*) FROM articles "
            "WHERE LENGTH(body_text) < ? AND repair_checked_at IS NULL AND section = ?",
            (MIN_PLAUSIBLE_BODY_CHARS, section),
        ).fetchone()[0]
    else:
        n = con.execute(
            "SELECT COUNT(*) FROM articles "
            "WHERE LENGTH(body_text) < ? AND repair_checked_at IS NULL",
            (MIN_PLAUSIBLE_BODY_CHARS,),
        ).fetchone()[0]
    con.close()
    return n


def get_unrepaired_short_articles(source_id, limit=200, section=None):
    """section lets a repair pass subset the queue (e.g. "opinion") instead
    of working through the whole backlog in insertion order -- economical
    when a specific slice is known to need attention."""
    con = connect(source_id)
    con.row_factory = sqlite3.Row
    if section:
        rows = con.execute(
            "SELECT id, url, date, body_text FROM articles "
            "WHERE LENGTH(body_text) < ? AND repair_checked_at IS NULL AND section = ? "
            "ORDER BY date DESC LIMIT ?",
            (MIN_PLAUSIBLE_BODY_CHARS, section, limit),
        ).fetchall()
    else:
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


# ── author backfill (added 2026-08-11) ───────────────────────────────────────
# WordPress exposes the real byline as a structured field (post.author ->
# _embedded.author[0].name), separate from body content, that the scraper
# never requested before. Existing rows predate that fix, so this sweeps
# them via cheap listing pages (url + author only, no full re-fetch).

def update_authors_bulk(source_id, url_author_pairs):
    """url_author_pairs: iterable of (url, author_name). Updates author only
    where it's currently empty/NULL, so a rerun is idempotent and cheap."""
    if not url_author_pairs:
        return 0
    con = connect(source_id)
    cur = con.executemany(
        "UPDATE articles SET author = ? WHERE url = ? AND (author IS NULL OR author = '')",
        [(author or "", url) for url, author in url_author_pairs],
    )
    con.commit()
    updated = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    con.close()
    return updated


def count_missing_author(source_id):
    con = connect(source_id)
    n = con.execute(
        "SELECT COUNT(*) FROM articles WHERE author IS NULL OR author = ''"
    ).fetchone()[0]
    con.close()
    return n


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
    init_db(source_id)  # ensures idx_articles_date/idx_articles_year/idx_articles_scraped_at exist -- see 2026-08-21 migration note above
    con = connect(source_id)
    # Split from one combined query: mixing MIN/MAX(date) with MAX(scraped_at)
    # stopped SQLite from using either index and forced a full table scan --
    # confirmed live via EXPLAIN QUERY PLAN ("SCAN articles"). Two separate
    # index-only queries instead of one scan.
    row = con.execute(
        "SELECT COUNT(*) n, MIN(date) mn, MAX(date) mx FROM articles"
    ).fetchone()
    last_scraped = con.execute("SELECT MAX(scraped_at) FROM articles").fetchone()[0]
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
        "last_scraped":  last_scraped,
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


# ── explorer: simple search/browse UI backend (added 2026-08-11) ────────────

def search_articles(source_id, query_str="", date_from="", date_to="", limit=25, offset=0):
    if not db_exists(source_id):
        return [], 0
    # Older imported DBs (e.g. the pendrive backfill) predate the
    # image_local_path/repair_checked_at column migrations -- run them
    # before querying, same fix as the /repair route needed.
    init_db(source_id)
    d_from = date_from or "0000-01-01"
    d_to = date_to or "9999-12-31"
    con = connect(source_id)
    con.row_factory = sqlite3.Row

    use_fts = bool(query_str)
    cols = "id, source, date, title, url, body_text, section, image_url, image_local_path, author"
    cols_a = ", ".join(f"a.{c}" for c in cols.split(", "))
    if use_fts:
        # Sorted by date below (like the no-query browse case), not FTS
        # relevance -- simpler and more predictable for "browse an archive"
        # than mixing two different sort semantics depending on whether a
        # query was typed.
        base = (
            f"SELECT {cols_a} FROM articles a JOIN articles_fts f ON a.id = f.rowid "
            "WHERE articles_fts MATCH ? AND a.date BETWEEN ? AND ?"
        )
        count_base = (
            "SELECT COUNT(*) FROM articles a JOIN articles_fts f ON a.id = f.rowid "
            "WHERE articles_fts MATCH ? AND a.date BETWEEN ? AND ?"
        )
        params = (query_str, d_from, d_to)
    else:
        base = f"SELECT {cols} FROM articles a WHERE a.date BETWEEN ? AND ?"
        count_base = "SELECT COUNT(*) FROM articles a WHERE a.date BETWEEN ? AND ?"
        params = (d_from, d_to)

    total = con.execute(count_base, params).fetchone()[0]
    rows = con.execute(
        base + " ORDER BY a.date DESC LIMIT ? OFFSET ?", params + (limit, offset)
    ).fetchall()
    con.close()
    out = [dict(r) for r in rows]
    for r in out:
        r["source_id"] = source_id  # the internal key (e.g. "laprensaaustral"),
                                     # distinct from r["source"] (display name)
    return out, total


def list_source_ids_with_data():
    """Every source that actually has a DB file, discovered from disk rather
    than a hardcoded list -- db.py doesn't otherwise know the full source
    roster (that lives in app.py's SOURCES), and this keeps it that way."""
    import glob
    paths = glob.glob(os.path.join(DATA_DIR, "yene_*.db"))
    return sorted(
        os.path.basename(p)[len("yene_"):-len(".db")]
        for p in paths
        if not p.endswith(".bak")  # skip backup copies like the elpinguino pre-repair one
    )


def search_all_sources(query_str="", date_from="", date_to="", limit=25, offset=0, source_ids=None):
    """Fans out to every source's own DB and merges by date. Simple, not
    maximally efficient (each source is queried for up to offset+limit rows
    even though most of that gets discarded after the merge) -- fine at this
    scale (a couple dozen local SQLite files), not built to paginate deep
    into a huge merged result set quickly.

    source_ids: restrict the fan-out to this explicit list instead of every
    DB file found on disk (e.g. app.py's regional-only explorer filter)."""
    need = offset + limit
    total = 0
    pooled = []
    for source_id in (source_ids if source_ids is not None else list_source_ids_with_data()):
        rows, count = search_articles(source_id, query_str, date_from, date_to, limit=need, offset=0)
        total += count
        pooled.extend(rows)
    pooled.sort(key=lambda r: r["date"], reverse=True)
    return pooled[offset:offset + limit], total


def iter_matching_articles(source_id, query_str="", date_from="", date_to=""):
    """Generator over EVERY matching row (no limit) -- for CSV export, where
    loading the whole result set into a list first (fetchall()) could mean
    hundreds of MB for a big source like elpinguino. Iterating the cursor
    directly stays lazy."""
    if not db_exists(source_id):
        return
    init_db(source_id)
    d_from = date_from or "0000-01-01"
    d_to = date_to or "9999-12-31"
    con = connect(source_id)
    con.row_factory = sqlite3.Row
    cols = "id, source, date, title, url, body_text, section, image_url, author"
    cols_a = ", ".join(f"a.{c}" for c in cols.split(", "))

    if query_str:
        cur = con.execute(
            f"SELECT {cols_a} FROM articles a JOIN articles_fts f ON a.id = f.rowid "
            "WHERE articles_fts MATCH ? AND a.date BETWEEN ? AND ? ORDER BY a.date DESC",
            (query_str, d_from, d_to),
        )
    else:
        cur = con.execute(
            f"SELECT {cols} FROM articles a WHERE a.date BETWEEN ? AND ? ORDER BY a.date DESC",
            (d_from, d_to),
        )
    for row in cur:
        d = dict(row)
        d["source_id"] = source_id
        yield d
    con.close()
