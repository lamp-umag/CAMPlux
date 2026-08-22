#!/usr/bin/env python3
"""
One-off, bounded test to pick BULK_WORKERS in scrapers/elpinguino.py
empirically instead of guessing. Fetches the same ~20 real article URLs at
1, 3, and 5 concurrent workers and times each. Not part of the running
app -- a measurement tool, run once, result recorded in a comment in
elpinguino.py itself.
"""
import sys
import time
import concurrent.futures as cf

sys.path.insert(0, "/home/mnx/camplux/vault")
from scrapers.elpinguino import ElPinguinoScraper, build_url

N_URLS = 20


def get_sample_urls(scraper, n=N_URLS):
    # A recent date with a full day's worth of real articles.
    _, items = scraper._fetch_day_raw(scraper.session, "2026-05-15", delay=0.3)
    urls = [build_url(item, "2026-05-15") for item in items[:n]]
    return urls


def timed_fetch(scraper, urls, workers):
    start = time.time()
    ok = 0
    if workers == 1:
        for u in urls:
            r = scraper._fetch_body(u, delay=0.5)
            if r and len(r[3]) > 150:
                ok += 1
    else:
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(scraper._fetch_body, u, 0.5) for u in urls]
            for f in cf.as_completed(futs):
                r = f.result()
                if r and len(r[3]) > 150:
                    ok += 1
    elapsed = time.time() - start
    return elapsed, ok


def main():
    scraper = ElPinguinoScraper()
    urls = get_sample_urls(scraper)
    print(f"Testing against {len(urls)} real article URLs\n")

    for workers in (1, 3, 5, 8):
        elapsed, ok = timed_fetch(scraper, urls, workers)
        rate = len(urls) / elapsed if elapsed else 0
        print(f"workers={workers:2d}  time={elapsed:6.1f}s  ok={ok}/{len(urls)}  "
              f"rate={rate:.2f} articles/s")


if __name__ == "__main__":
    main()
