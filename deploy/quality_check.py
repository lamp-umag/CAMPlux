"""
One-shot overnight quality audit across every source with real data --
sleeps until a fixed time (after both ovejero_gapfill's nightly window and
the 03:00 nightly-archive timer are expected to be done), then runs a
bounded random-sample sanity pass. Source list is discovered live from the
running app (get_all_sources()), not hardcoded -- originally only covered
the 11 Magallanes sources, widened 2026-08-22 when the national expansion
campaign (see deploy/expansion/) landed 100+ more sources across 14 other
regions. Run with --now to skip the sleep for a manual/on-demand run:

    python3 deploy/quality_check.py --now

  1. Site/API health probe per source (catches something like zonazero's
     WP REST API going 404 site-wide, observed live 2026-08-11 evening --
     unrelated to any of our code, but worth confirming it recovered).
  2. For a random sample of already-stored articles per source: refetch the
     live URL and flag anything that smells wrong -- HTTP error, a
     Cloudflare/anti-bot challenge page instead of the real article, a
     response that's suspiciously short, or a stored title that no longer
     appears anywhere in the live page (could mean the URL now points to
     different/replaced content).

This is a smoke test, not a full re-scrape or content diff -- cheap and
bounded on purpose. Findings go to deploy/logs_quality_check.log and a
JSON summary at deploy/.quality_check_report.json for the next session to
read cold.
"""
import datetime
import json
import os
import re
import subprocess
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(HERE, ".quality_check_report.json")

# The real DBs live in the vault_data Docker named volume, not any host
# path -- sampling has to go through the running container (confirmed live:
# a first version of this script pointed at vault/data on the host and
# silently sampled 0 articles from every source).
CONTAINER = "camplux-vault-1"

RUN_AT_HOUR = 5  # local time -- after the 03:00 nightly-archive timer
SAMPLE_SIZE = 8
TIMEOUT = 15

# Matches vault/scrapers/base.py's HEADERS -- several of these sites 403/406
# a generic python-requests UA, so use the same identifying UA the real
# scraper sends day to day (confirmed live 2026-08-11: pepenoticias,
# sosmagallanes, radiomagallanes all reject the bare default UA).
UA = ("camplux-Quarry/1.0 (academic corpus research, Magallanes media; "
      "contact: culpem@research.local)")
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Deliberately specific to actual interstitial challenge/block pages, not
# "captcha" alone -- that false-positived on completely normal articles
# whose comment form or Akismet widget just mentions reCAPTCHA (confirmed
# live 2026-08-11: radiomagallanes/sosmagallanes/itvpatagonia samples all
# 200'd with the real ~200KB+ article; "captcha" was just noise from that).
CHALLENGE_MARKERS = (
    "just a moment", "attention required", "cf-browser-verification",
    "checking your browser before accessing",
    "acceso denegado", "access denied", "verificando que usted es un ser humano",
)

# Was a hardcoded 11-entry dict (Magallanes only) -- as of the 2026-08-22
# national expansion (see deploy/expansion/), that would silently skip 100+
# new sources across 14 other regions. Replaced with dynamic discovery from
# the live app (get_all_sources()) + a health-check URL derived from each
# source's own sample article domain (get_health_check_cfg()), so this
# script needs no manual update as more sources get added. A couple of
# sources need a special-cased health URL because they're not a plain WP
# REST API (elpinguino is Cloudflare-protected and exposes a different
# search endpoint; radiopolar isn't WordPress at all) -- kept as explicit
# overrides rather than trying to make the generic path handle every case.
SPECIAL_HEALTH_URLS = {
    "elpinguino": {"api": "https://elpinguino.com/v2/home/search/{today}"},
    "radiopolar": {"api": "https://www.radiopolar.com/"},
    "itvpatagonia": {"browser_ua": True},  # generic URL, just needs a browser UA
}

VAULT_BASE = "http://127.0.0.1:5001"


def get_all_sources():
    """Every source with real data, discovered live from the running app --
    not a hardcoded list. Skips sources that exist but have 0 rows (never
    backfilled, e.g. theclinic) since there's nothing to sample."""
    r = requests.get(f"{VAULT_BASE}/status", timeout=15)
    r.raise_for_status()
    status = r.json()
    return sorted(sid for sid, info in status.items()
                  if info.get("exists") and info.get("count", 0) > 0)


def log(msg):
    print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def sleep_until_target():
    now = datetime.datetime.now()
    target = now.replace(hour=RUN_AT_HOUR, minute=0, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    secs = (target - now).total_seconds()
    log(f"Sleeping {secs/3600:.1f}h until {target.isoformat(timespec='minutes')}")
    time.sleep(secs)


def check_api_health(source_id, cfg, sample_url):
    headers = {"User-Agent": BROWSER_UA if cfg.get("browser_ua") else UA,
               "Accept-Language": "es-CL,es;q=0.9,en;q=0.5"}
    if "api" in cfg:
        url = cfg["api"].format(today=datetime.date.today().isoformat())
    elif sample_url:
        # Derive the health-check URL from a real sample article's own
        # domain -- works for any WordPress source without needing it
        # hardcoded, and stays correct even if a site changes its own
        # base_url (the scraper config might lag, a stored article URL
        # won't).
        from urllib.parse import urlsplit
        parts = urlsplit(sample_url)
        url = f"{parts.scheme}://{parts.netloc}/wp-json/wp/v2/posts?per_page=1"
    else:
        return {"ok": False, "status": None, "url": None, "error": "no sample URL to derive a health check from"}
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
        ok = r.status_code == 200 and (
            "json" in r.headers.get("Content-Type", "") or source_id == "radiopolar"
        )
        return {"ok": ok, "status": r.status_code, "url": url}
    except Exception as e:
        return {"ok": False, "status": None, "url": url, "error": str(e)}


_SAMPLE_SNIPPET = """
import json, db
con = db.connect({source_id!r})
rows = con.execute(
    "SELECT id, title, url, LENGTH(body_text) AS body_len "
    "FROM articles ORDER BY RANDOM() LIMIT {n}"
).fetchall()
print(json.dumps([dict(zip(['id','title','url','body_len'], r)) for r in rows]))
"""


def sample_articles(source_id, n):
    snippet = _SAMPLE_SNIPPET.format(source_id=source_id, n=n)
    try:
        out = subprocess.run(
            ["docker", "exec", CONTAINER, "python3", "-c", snippet],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return json.loads(out.stdout.strip() or "[]")
    except Exception as e:
        log(f"  ⚠ {source_id}: couldn't sample from container DB: {e}")
        return []


def check_live_article(source_id, art, cfg):
    headers = {"User-Agent": BROWSER_UA if cfg.get("browser_ua") else UA,
               "Accept-Language": "es-CL,es;q=0.9,en;q=0.5"}
    try:
        r = requests.get(art["url"], headers=headers, timeout=TIMEOUT, allow_redirects=True)
    except Exception as e:
        return {"issue": f"fetch error: {e}"}

    # A handful of sources block the plain UA with a WAF (confirmed live
    # during the expansion campaign for madero/elrancaguino, both of which
    # need a per-source scraper UA override to actually work) -- this
    # script doesn't have access to each scraper's exact override, so
    # retry once with a browser UA before treating a 403 as real. Cuts
    # down false positives without needing per-source scraper introspection.
    if r.status_code == 403 and not cfg.get("browser_ua"):
        try:
            r = requests.get(art["url"], headers={**headers, "User-Agent": BROWSER_UA},
                              timeout=TIMEOUT, allow_redirects=True)
        except Exception:
            pass

    if r.status_code >= 400:
        return {"issue": f"HTTP {r.status_code}"}

    text_lower = r.text.lower()
    for marker in CHALLENGE_MARKERS:
        if marker in text_lower:
            return {"issue": f"possible challenge/anti-bot page (marker: {marker!r})"}

    if len(r.text) < 500:
        return {"issue": f"suspiciously short live response ({len(r.text)} bytes)"}

    title = (art.get("title") or "").strip()
    if title:
        # Loose check: at least a meaningful chunk of the title's words show
        # up somewhere on the page. Not exact -- titles get truncated/edited
        # in <title>/og:title all the time -- just a "is this even the same
        # article" smoke test.
        words = [w for w in re.findall(r"\w{4,}", title.lower())][:6]
        hits = sum(1 for w in words if w in text_lower)
        if words and hits < max(1, len(words) // 3):
            return {"issue": f"stored title barely matches live page content "
                              f"({hits}/{len(words)} words found)"}

    if (art.get("body_len") or 0) < 150:
        return {"issue": f"stored body_text still short ({art.get('body_len')} chars) "
                          f"but live page looks fine -- repair candidate"}

    return None


def run():
    report = {"run_at": datetime.datetime.now().isoformat(), "sources": {}}
    sources = get_all_sources()
    log(f"Discovered {len(sources)} sources with data (live from {VAULT_BASE}/status)")

    for source_id in sources:
        cfg = SPECIAL_HEALTH_URLS.get(source_id, {})
        log(f"=== {source_id} ===")

        samples = sample_articles(source_id, SAMPLE_SIZE)
        sample_url = samples[0]["url"] if samples else None
        health = check_api_health(source_id, cfg, sample_url)
        if not health["ok"]:
            log(f"  ⚠ API/site health check failed: {health}")
        else:
            log(f"  ✓ API/site health OK ({health['status']})")

        issues = []
        for art in samples:
            result = check_live_article(source_id, art, cfg)
            time.sleep(0.5)
            if result:
                issues.append({"id": art["id"], "url": art["url"], **result})
                log(f"  ⚠ id={art['id']} {result['issue']} -- {art['url']}")

        if samples and not issues:
            log(f"  ✓ {len(samples)}/{len(samples)} sampled articles look fine")

        report["sources"][source_id] = {
            "health": health,
            "sampled": len(samples),
            "issues": issues,
        }

    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log(f"Report written to {REPORT_PATH}")
    log("Quality check complete.")


if __name__ == "__main__":
    import sys
    if "--now" not in sys.argv:
        sleep_until_target()
    run()
