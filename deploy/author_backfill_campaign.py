"""
One-off backfill of the new `author` column for existing Magallanes rows
(see scrapers/wordpress.py's run_author_backfill / app.py's
/authors/backfill). Existing rows predate the fix that started requesting
WordPress's structured author field -- this sweeps them via cheap listing
pages (url + author only), no full re-scrape.

Only WP-based Magallanes sources have a backfill path (El Pingüino and
Radio Polar don't expose an equivalent reliable structured field -- see
commit b751013). Runs sequentially, source by source, through the local
Vault API's own /authors/backfill SSE endpoint (which holds the per-source
lock for the duration), so it can't collide with a manual action on the
same source. Expected total runtime ~30-40 min for ~172k rows at this
host's measured WP API throughput -- small enough to just run once, live,
rather than needing multi-night checkpointing like ovejero_gapfill.

Launched detached (nohup ... & disown). Logs to
deploy/logs_author_backfill.log.
"""
import datetime
import json
import sys
import time
import urllib.request

BASE = "http://localhost:5001"

SOURCES = [
    "dialogosur", "ovejeronoticias", "elmagallanico", "pepenoticias",
    "zonazero", "itvpatagonia", "sosmagallanes", "radiomagallanes",
    "laprensaaustral",
]


def log(msg):
    print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def run_source(source_id):
    url = f"{BASE}/authors/backfill?source={source_id}"
    log(f"=== {source_id}: starting ===")
    checked = updated = remaining = None
    try:
        with urllib.request.urlopen(url, timeout=1800) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data: "):
                    continue
                ev = json.loads(line[len("data: "):])
                t = ev.get("type")
                if t == "log":
                    log(f"  {source_id}: {ev.get('msg')}")
                elif t == "progress" and ev.get("page", 0) % 20 == 0:
                    log(f"  {source_id}: page {ev.get('page')}/{ev.get('total_pages')} "
                        f"checked={ev.get('checked')} updated={ev.get('updated')}")
                elif t == "done":
                    checked, updated, remaining = ev.get("checked"), ev.get("updated"), ev.get("remaining")
    except Exception as e:
        log(f"  {source_id}: ERROR {e!r}")
        return
    log(f"=== {source_id}: done -- checked={checked} updated={updated} remaining={remaining} ===")


def main():
    log(f"Author backfill campaign starting, {len(SOURCES)} sources: {SOURCES}")
    for source_id in SOURCES:
        run_source(source_id)
        time.sleep(2)
    log("Campaign complete.")


if __name__ == "__main__":
    main()
