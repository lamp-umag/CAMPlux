"""
One-off historical backfill for ovejeronoticias' 2017-2025 gap (~43k posts
missing -- the automated nightly system was dormant for those years, this
isn't a scraper bug). See project memory / conversation from 2026-08-11.

The site's own WP REST API is slow/flaky on these deep date-range queries
(measured live: ~1 post/sec including retries, vs. the ~60-100/sec a
healthy WP API should give -- their server, not our code). Rather than one
giant blocking call, this walks the gap year by year against the local
Vault API (mode=range), with a real wall-clock ceiling per night so it
never runs past the 03:00 nightly-archive timer. A completed-years marker
file makes it safely resumable across as many nights as it actually takes
-- re-running an already-slow year over again would just waste another
slow night for nothing.

Launched detached (nohup ... & disown), not tied to any conversation
session. Logs to deploy/logs_ovejero_gapfill.log.
"""
import datetime
import json
import os
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRESS_FILE = os.path.join(HERE, ".ovejero_gapfill_progress.json")
LOG_FILE = os.path.join(HERE, "logs_ovejero_gapfill.log")

VAULT_URL = "http://localhost:5001/archive"
SOURCE = "ovejeronoticias"

# The full gap, split into year-sized chunks so a bad night only costs one
# year's worth of slow retries, not the whole 8.75-year span.
YEAR_CHUNKS = [
    (2017, "2017-01-01", "2017-12-31"),
    (2018, "2018-01-01", "2018-12-31"),
    (2019, "2019-01-01", "2019-12-31"),
    (2020, "2020-01-01", "2020-12-31"),
    (2021, "2021-01-01", "2021-12-31"),
    (2022, "2022-01-01", "2022-12-31"),
    (2023, "2023-01-01", "2023-12-31"),
    (2024, "2024-01-01", "2024-12-31"),
    (2025, "2025-01-01", "2025-09-30"),
]

START_AT_HOUR = 21          # 21:00 local -- clear of normal daytime use
NIGHT_CEILING_SECONDS = 5.5 * 3600   # stop well before the 03:00 nightly-archive timer
PER_YEAR_TIMEOUT_SECONDS = 3600      # a single year chunk shouldn't run forever either


def log(msg):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return set(json.load(f))
    return set()


def save_progress(done_years):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(sorted(done_years), f)


def sleep_until_start():
    now = datetime.datetime.now()
    target = now.replace(hour=START_AT_HOUR, minute=0, second=0, microsecond=0)
    if now >= target:
        target += datetime.timedelta(days=1)
    wait_s = (target - now).total_seconds()
    log(f"Sleeping {wait_s/3600:.1f}h until {target.isoformat(timespec='minutes')}")
    time.sleep(wait_s)


def run_year_chunk(year, date_from, date_to):
    log(f"--- {SOURCE} {year}: {date_from} -> {date_to} ---")
    params = {"source": SOURCE, "mode": "range", "date_from": date_from,
              "date_to": date_to, "delay": "1.0"}
    try:
        with requests.get(VAULT_URL, params=params, stream=True,
                           timeout=PER_YEAR_TIMEOUT_SECONDS) as r:
            last_event = None
            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                try:
                    evt = json.loads(raw_line[len("data: "):])
                except ValueError:
                    continue
                if evt.get("type") == "log":
                    log(f"  [{evt.get('level')}] {evt.get('msg')}")
                elif evt.get("type") == "progress":
                    last_event = evt
                elif evt.get("type") == "done":
                    last_event = evt
                    log(f"  done: seen={evt.get('seen')} saved={evt.get('saved')} "
                        f"total_db={evt.get('total_db')} job_status={evt.get('job_status')}")
                elif evt.get("type") == "failed_pages":
                    log(f"  {evt.get('msg')}")
            return last_event
    except requests.exceptions.Timeout:
        log(f"  ✗ year {year} exceeded its {PER_YEAR_TIMEOUT_SECONDS}s ceiling -- "
            f"moving on, will retry another night")
        return None
    except requests.RequestException as e:
        log(f"  ✗ year {year} request error: {e}")
        return None


def main():
    sleep_until_start()
    session_start = time.time()
    done_years = load_progress()
    log(f"Starting session. Already-completed years: {sorted(done_years) or 'none'}")

    for year, date_from, date_to in YEAR_CHUNKS:
        if year in done_years:
            log(f"Skipping {year} (already completed a prior night)")
            continue
        if time.time() - session_start > NIGHT_CEILING_SECONDS:
            log("Hit tonight's time ceiling -- stopping, will resume tomorrow night")
            break

        result = run_year_chunk(year, date_from, date_to)
        if result and result.get("type") == "done" and not result.get("job_status") == "locked":
            # Mark complete only if nothing failed outright -- a few skipped
            # pages within the year is an accepted, already-logged limitation
            # of the underlying scraper, not worth blocking future nights on.
            done_years.add(year)
            save_progress(done_years)
        else:
            log(f"  {year} not marked complete -- will retry another night")

    if len(done_years) == len(YEAR_CHUNKS):
        log("All years complete. Gap-fill finished.")
    else:
        remaining = [y for y, _, _ in YEAR_CHUNKS if y not in done_years]
        log(f"Session ended. Remaining years: {remaining}")


if __name__ == "__main__":
    main()
