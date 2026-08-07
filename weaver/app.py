import csv
import json
import logging
import tempfile
from pathlib import Path

import pandas as pd
from flask import Flask, Response, jsonify, render_template, request, send_file
from flask import stream_with_context
from waitress import serve

import network
import yene_io

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app     = Flask(__name__)
HERE    = Path(__file__).parent
OUT_DIR = HERE / "output"
UPL_DIR = HERE / "uploads"
OUT_DIR.mkdir(exist_ok=True)
UPL_DIR.mkdir(exist_ok=True)

# Sister app — auto-detected; graceful if absent
CULPEM_DIR = HERE.parent / "quarry" / "output"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    culpem_present = CULPEM_DIR.exists()
    return render_template("index.html", culpem_present=culpem_present)


@app.route("/files")
def list_files():
    """Available CSV files from quarry output dir + local uploads."""
    result = {"culpem": [], "uploads": []}

    for label, directory, pattern in [
        ("culpem", CULPEM_DIR, "culpem_*.csv"),
        ("uploads", UPL_DIR,   "*.csv"),
    ]:
        if not directory.exists():
            continue
        for f in sorted(directory.glob(pattern),
                        key=lambda x: x.stat().st_mtime, reverse=True):
            info = _file_info(f)
            result[label].append(info)

    # Yene archives (SQLite) appear under their own group; path == name so the
    # /build handler can detect them via yene_io.is_yene_name and materialize.
    result["yene"] = []
    for entry in yene_io.list_yene_sources():
        meta = entry.get("meta", {})
        result["yene"].append({
            "name":     entry["name"],
            "path":     entry["name"],     # pseudo-path; resolved in /build
            "count":    meta.get("n_articles", "?"),
            "sources":  [meta.get("source_id", "")],
            "date_min": meta.get("min_date"),
            "date_max": meta.get("max_date"),
        })

    return jsonify(result)


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f or not f.filename.endswith(".csv"):
        return jsonify({"error": "CSV file required"}), 400
    safe = "".join(c for c in f.filename if c.isalnum() or c in "._-")
    if not safe.endswith(".csv"):
        safe += ".csv"
    dest = UPL_DIR / safe
    f.save(dest)
    return jsonify({"ok": True, **_file_info(dest)})


@app.route("/build")
def build():
    files = request.args.getlist("files")
    if not files:
        return jsonify({"error": "No files selected"}), 400

    # Materialize any Yene pseudo-paths into temp CSVs so network.build (which
    # only knows pd.read_csv) doesn't need to learn about SQLite.
    resolved_files = []
    tmp_paths = []
    for f in files:
        name = Path(f).name
        if yene_io.is_yene_name(name):
            rows = yene_io.load_yene_rows(name)
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=f"_{name}.csv", delete=False,
                encoding="utf-8-sig", newline="",
            )
            if rows:
                writer = csv.DictWriter(tmp, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            tmp.close()
            tmp_paths.append(Path(tmp.name))
            resolved_files.append(tmp.name)
        else:
            resolved_files.append(f)
    files = resolved_files

    settings = {k: request.args.get(k, v) for k, v in {
        "min_doc_freq":     "30",
        "min_jaccard":      "0.12",
        "min_word_len":     "4",
        "lemmatization":    "1",
        "ngrams":           "1",
        "phrase_min_count": "15",
        "phrase_threshold": "8",
        "extra_stopwords":  "",
    }.items()}

    def generate():
        try:
            for event in network.build(files, settings, OUT_DIR):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            app.logger.exception("network.build failed")
            yield f"data: {json.dumps({'type':'log','level':'error','msg':str(e)})}\n\n"
            yield f"data: {json.dumps({'type':'done','error':str(e)})}\n\n"
        finally:
            for p in tmp_paths:
                try: p.unlink()
                except Exception: pass

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/download/<filename>")
def download(filename):
    if not filename.startswith("dewu_") or ".." in filename or "/" in filename:
        return "Not found", 404
    fp = OUT_DIR / filename
    if not fp.exists():
        return "Not found", 404
    return send_file(fp, as_attachment=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _file_info(path: Path) -> dict:
    info = {"name": path.name, "path": str(path), "count": "?",
            "sources": [], "date_min": None, "date_max": None}
    try:
        df = pd.read_csv(path, encoding="utf-8-sig",
                         usecols=lambda c: c in {"source", "date", "url"})
        info["count"]    = len(df)
        info["sources"]  = sorted(df["source"].dropna().unique().tolist()) \
                           if "source" in df.columns else []
        info["date_min"] = str(df["date"].min()) if "date" in df.columns else None
        info["date_max"] = str(df["date"].max()) if "date" in df.columns else None
    except Exception:
        pass
    return info


if __name__ == "__main__":
    # waitress, not Flask's dev server: debug=True exposes an interactive
    # Python console on unhandled exceptions -- fine on localhost-only, a
    # real problem once this is reachable beyond localhost.
    serve(app, host="0.0.0.0", port=5005, threads=4)
