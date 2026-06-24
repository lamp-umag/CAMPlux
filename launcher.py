"""
CAMPlux — Beacon launcher.

Beacon is the suite's control tower: it starts every CAMPlux module as a
subprocess (each a small Flask app on its own port) and serves a status
dashboard at http://localhost:5050 that shows which modules are up.

Modules start in dependency order — Vault (storage) first so its database
layer is ready before the scraper and downstream analysis tools come online.

Because this is a monorepo, each module lives in a subfolder of this file's
directory (vault/, quarry/, …). Ctrl+C shuts everything down cleanly.
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from threading import Thread

import requests
from flask import Flask, jsonify, render_template

HERE           = Path(__file__).parent.resolve()
DASHBOARD_PORT = 5050   # 5000 is taken by macOS AirPlay Receiver by default

# Startup order matters: Vault (the data layer) initializes first.
APPS = [
    {
        "id": "vault", "name": "CAMPlux-Vault", "dir": "vault", "port": 5001,
        "emoji": "🐋", "accent": "#2e7fd8",
        "desc": "Archivo local persistente de medios (storage)",
    },
    {
        "id": "quarry", "name": "CAMPlux-Quarry", "dir": "quarry", "port": 5002,
        "emoji": "🦊", "accent": "#e8733a",
        "desc": "Scraper de medios para construir corpus (acquisition)",
    },
    {
        "id": "cleaner", "name": "CAMPlux-Cleaner", "dir": "cleaner", "port": 5003,
        "emoji": "🐱", "accent": "#d4a86a",
        "desc": "Limpieza, deduplicación y estandarización de textos",
    },
    {
        "id": "prism", "name": "CAMPlux-Prism", "dir": "prism", "port": 5004,
        "emoji": "🐍", "accent": "#8bc44c",
        "desc": "Análisis LLM: sentimiento, contenido, preguntas sí/no",
    },
    {
        "id": "weaver", "name": "CAMPlux-Weaver", "dir": "weaver", "port": 5005,
        "emoji": "🕷️", "accent": "#3aab8f",
        "desc": "Red de conceptos / matriz para Gephi",
    },
    {
        "id": "stats", "name": "CAMPlux-Stats", "dir": "stats", "port": 5006,
        "emoji": "🦅", "accent": "#9b7dd4",
        "desc": "Análisis estadístico del corpus",
    },
]

processes = []   # (app_id, Popen) tuples


# ── App lookup & launching ────────────────────────────────────────────────────

def find_app_dir(app_dirname: str) -> Path | None:
    """Module folder inside the monorepo (with a sibling-dir fallback for dev)."""
    for c in (HERE / app_dirname, HERE.parent / app_dirname):
        if c.exists() and (c / "app.py").exists():
            return c
    return None


def start_app(app: dict) -> subprocess.Popen | None:
    app_dir = find_app_dir(app["dir"])
    if not app_dir:
        print(f"  ⚠ {app['name']}: no encontrado en {app['dir']}/")
        return None

    log_path = HERE / "logs" / f"{app['id']}.log"
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(app_dir),
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        stdout=open(log_path, "ab"),
        stderr=subprocess.STDOUT,
    )
    print(f"  → {app['emoji']} {app['name']} (PID {proc.pid}) :{app['port']}")
    return proc


def cleanup():
    if not processes:
        return
    print("\nApagando CAMPlux…")
    for _, p in processes:
        if p and p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
    print("Bye! 🐾")


# ── Dashboard Flask app ───────────────────────────────────────────────────────

flask_app = Flask(__name__)


@flask_app.route("/")
def index():
    return render_template("index.html", apps=APPS)


@flask_app.route("/status")
def status():
    result = {}
    for app in APPS:
        app_dir   = find_app_dir(app["dir"])
        installed = app_dir is not None
        running   = False
        if installed:
            try:
                r = requests.get(f"http://localhost:{app['port']}/", timeout=0.4)
                running = r.status_code < 500
            except Exception:
                running = False
        result[app["id"]] = {"installed": installed, "running": running}
    return jsonify(result)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    (HERE / "logs").mkdir(exist_ok=True)

    print("🐾 CAMPlux — Beacon iniciando la suite")
    print("=" * 50)

    for app in APPS:
        p = start_app(app)
        if p:
            processes.append((app["id"], p))

    print(f"\n  → 🏠 Dashboard (Beacon):  http://localhost:{DASHBOARD_PORT}")
    print(f"     Logs:                  {HERE / 'logs'}")
    print("\n  Ctrl+C para detener todo.\n")

    def _open():
        time.sleep(2.5)
        try: webbrowser.open(f"http://localhost:{DASHBOARD_PORT}")
        except Exception: pass
    Thread(target=_open, daemon=True).start()

    try:
        flask_app.run(host="127.0.0.1", port=DASHBOARD_PORT,
                      debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
