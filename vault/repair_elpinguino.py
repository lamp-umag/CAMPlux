"""
Repair El Pingüino articles that were scraped with the broken pre-2026-06 code,
which only saved the API excerpt instead of the full body for pre-2014 articles
(old URL format /noticias/{ID}, served by a different page template).

Usage:
  cd vault
  python3 repair_elpinguino.py           # dry-run (shows what would be fixed)
  python3 repair_elpinguino.py --do      # actually fix

Heuristic for "broken" rows:
  - URL matches the old format /noticias/{numeric ID}
  - body_text is empty OR shorter than 400 chars (real bodies are typically 800-2000+)

Refetches each broken article with the now-fixed scraper and updates the row,
also populating the new image_url column.
"""
import argparse
import os
import sqlite3
import sys
import time

# Allow running both as `python3 repair_elpinguino.py` from inside vault,
# and as `python3 vault/repair_elpinguino.py` from the suite root.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from scrapers.elpinguino import ElPinguinoScraper
import db as ydb

SOURCE_ID  = "elpinguino"
DB_PATH    = os.path.join(ydb.DATA_DIR, f"yene_{SOURCE_ID}.db")
SHORT_BODY = 400   # below this we suspect a truncated excerpt


def find_broken(con):
    rows = con.execute("""
        SELECT id, url, title, length(body_text) AS bl
        FROM articles
        WHERE url LIKE 'https://www.elpinguino.com/noticias/%'
          AND (body_text IS NULL OR length(body_text) < ?)
        ORDER BY date
    """, (SHORT_BODY,)).fetchall()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--do", action="store_true", help="actually update rows (without this it's a dry run)")
    ap.add_argument("--limit", type=int, default=0, help="cap the number of rows processed (0 = all)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between HTTP requests")
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        sys.exit(1)

    # Run migration first so image_url column exists on legacy DBs
    ydb.init_db(SOURCE_ID)

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    broken = find_broken(con)
    total = len(broken)
    if args.limit:
        broken = broken[: args.limit]

    print(f"Found {total} suspect rows (body < {SHORT_BODY} chars on old-URL articles)")
    if not broken:
        return
    print(f"Will process: {len(broken)}  (dry-run={not args.do})")
    print()

    scraper = ElPinguinoScraper()
    fixed = same = failed = 0

    for i, row in enumerate(broken, 1):
        try:
            result = scraper._fetch_body(row["url"], delay=args.delay)
        except Exception as e:
            print(f"  [{i}/{len(broken)}] ERR  {row['url']}: {e}")
            failed += 1
            continue

        if not result:
            print(f"  [{i}/{len(broken)}] 404  {row['url']}")
            failed += 1
            continue

        _t, _d, _s, body, image = result
        new_len = len(body)

        if new_len <= row["bl"]:
            print(f"  [{i}/{len(broken)}] ={new_len}  no improvement, leaving — {row['title'][:50]}")
            same += 1
            continue

        print(f"  [{i}/{len(broken)}] ✓ {row['bl']:>4}→{new_len:<4} chars  img={'Y' if image else '·'}  {row['title'][:50]}")

        if args.do:
            con.execute(
                "UPDATE articles SET body_text = ?, image_url = ? WHERE id = ?",
                (body, image, row["id"]),
            )
            con.commit()
        fixed += 1

    con.close()
    print()
    print(f"Done. Improved: {fixed}  ·  Unchanged: {same}  ·  Failed: {failed}")
    if not args.do:
        print("Dry-run only. Re-run with --do to actually write changes.")


if __name__ == "__main__":
    main()
