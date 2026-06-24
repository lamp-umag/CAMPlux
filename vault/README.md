# 🐋 YeneConservatio

**MolfunCognitio — Fauna del Saber**

Archivo local de medios regionales magallánicos. La ballena guarda todo.

One SQLite database per source. Each DB is a complete local mirror of that
source's article archive, from its earliest known record to today.

## Part of the suite

| App | Animal | Role |
|---|---|---|
| [CulpemCorpus](../CulpemCorpus) | 🦊 Zorro culpeo | Scrape & search on demand |
| **YeneConservatio** | 🐋 Ballena | Full local archive, persistent storage |

## Setup

```bash
pip install -r requirements.txt
python3 app.py
# Open http://localhost:5002
```

## How it works

- **Download / Update** — fetches new articles from the source's last known date to today. Safe to run repeatedly; duplicates are silently skipped.
- **Full re-scrape** — re-scrapes everything from the known archive start date. Use this to backfill or rebuild a DB.
- **Dedup** — `url` is a `UNIQUE` key in SQLite; `INSERT OR IGNORE` prevents duplicates.

## Archive start dates

| Source | Records from |
|---|---|
| El Pingüino | 2009-01-01 |
| Diálogo Sur | 2010-05-20 |
| Ovejero Noticias | 2015-07-17 |
| El Magallánico | 2017-07-11 |
| La Prensa Austral | 2020-01-30 |
| Pepe Noticias | 2020-07-14 |
| ITV Patagonia | 2023-07-01 |
| SOS Magallanes | 2025-05-01 |
| Radio Magallanes | 2025-11-04 |

## Data

DBs are stored in `data/yene_{source}.db`. The `data/` folder is gitignored —
the code is shareable; the archive is yours.

## DB schema

```sql
articles (
  id          INTEGER PRIMARY KEY,
  source      TEXT,
  date        TEXT,       -- YYYY-MM-DD
  title       TEXT,
  url         TEXT UNIQUE,
  body_text   TEXT,
  section     TEXT,
  scraped_at  TEXT        -- UTC ISO timestamp
)
-- FTS5 virtual table on title + body_text (auto-synced via triggers)
articles_fts USING fts5(title, body_text, content=articles)
```

Query example (SQLite CLI or any SQLite browser):
```sql
-- Full-text search
SELECT date, title, url FROM articles
JOIN articles_fts ON articles.id = articles_fts.rowid
WHERE articles_fts MATCH 'hidrógeno verde'
ORDER BY date DESC;

-- Articles per year
SELECT substr(date,1,4) as year, COUNT(*) FROM articles GROUP BY year;
```
