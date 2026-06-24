# 🐾 CAMPlux

**Corpus Acquisition & Media Processing** toolkit, with a lightweight user experience.
**Corpus y Análisis de Medios de Prensa.**

A suite of small, focused web apps for building and analysing press-media
corpora — developed at **LAMP UMAG** (Laboratorio Austral de Medición
Psicosocial, Universidad de Magallanes). Each module does one job, runs as a
local Flask app on its own port, and hands its output to the next. The
**Beacon** dashboard launches and monitors them all.

> CAMPlux is the successor to the `MolfunCognitio` / `KullinCognitio` prototype
> suite. The original animal-named modules live on as the icons you'll see in
> the dashboard. 🦊🐋🕷️🐱🦅🐍

---

## The six modules

| | Module | Folder | Port | Does |
|--|--|--|--|--|
| 🐋 | **CAMPlux-Vault**    | `vault/`   | 5001 | Local persistent archive (SQLite, one DB per source, full-text search). The data layer. |
| 🦊 | **CAMPlux-Quarry**   | `quarry/`  | 5002 | Media scraper. Builds corpora from news sources; reads Vault as a cache. |
| 🐱 | **CAMPlux-Cleaner**  | `cleaner/` | 5003 | Cleaning, deduplication and text standardisation of scraped CSVs. |
| 🐍 | **CAMPlux-Prism**    | `prism/`   | 5004 | LLM analysis (via Ollama): sentiment, content classification, yes/no questions. |
| 🕷️ | **CAMPlux-Weaver**   | `weaver/`  | 5005 | Concept co-occurrence networks → GEXF matrices for Gephi. |
| 🦅 | **CAMPlux-Stats**    | `stats/`   | 5006 | Statistical analysis of the corpus. |
| 🐾 | **Beacon** (launcher) | *(root)*  | 5050 | Dashboard + process manager. Starts everything, shows live status. |

---

## Data flow

```
        ┌─────────┐   scrapes    ┌──────────┐
  web → │ Quarry  │ ───────────► │  Vault   │  (SQLite archive, FTS5)
        │ 🦊 5002 │ ◄─ cache ──  │ 🐋 5001  │
        └────┬────┘              └────┬─────┘
             │ CSV                    │ DBs
             ▼                        ▼
        ┌─────────┐            (all downstream modules can read Vault directly)
        │ Cleaner │ 🐱 5003  → cleaned/deduped CSV
        └────┬────┘
             ├──────────────┬───────────────┐
             ▼              ▼               ▼
        ┌─────────┐   ┌──────────┐    ┌──────────┐
        │  Prism  │   │  Weaver  │    │  Stats   │
        │ 🐍 5004 │   │ 🕷️ 5005 │    │ 🦅 5006  │
        └─────────┘   └──────────┘    └──────────┘
         sentiment    Gephi network    statistics
```

Modules discover each other's output by convention: each writes timestamped
CSVs (`culpem_*.csv`, `narki_*.csv`, `filu_*.csv` — internal data tokens kept
from the prototype) into its own `output/` folder, and the next module reads
from the sibling folder. Everything is local; nothing leaves your machine
except the scraper's HTTP requests to news sites and Prism's calls to your
local Ollama instance.

---

## Quick start

```bash
git clone https://github.com/lamp-umag/camplux.git
cd camplux

# Easiest: double-click start.command (macOS) or start.bat (Windows).
# Or from a terminal:
python3 run.py
```

`run.py` creates a `.venv`, installs every module's dependencies, then starts
Beacon. Your browser opens at **http://localhost:5050** with a card per module.
Click **Abrir →** on any running module to use it.

### Manual setup (if you prefer)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
for m in vault quarry cleaner prism weaver stats; do
  pip install -r $m/requirements.txt
done
python -m spacy download es_core_news_sm   # for Weaver
python launcher.py
```

### Prism needs Ollama

CAMPlux-Prism calls a local [Ollama](https://ollama.com) server for LLM
analysis. Install it, then:

```bash
ollama serve            # leave running (listens on :11434)
ollama pull llama3.2    # or any model you prefer
```

---

## Bringing your existing archive

Vault's scraped databases (`vault/data/*.db`) are **not** in this repo — they're
data, can be gigabytes, and are git-ignored. If you have an archive from the
prototype suite, copy it in once:

```bash
cp -R /path/to/old/YeneConservatio/data/ vault/data/
```

Otherwise Quarry/Vault will simply build a fresh archive as you scrape.

---

## Ports

| Service | Port |
|--|--|
| Vault | 5001 |
| Quarry | 5002 |
| Cleaner | 5003 |
| Prism | 5004 |
| Weaver | 5005 |
| Stats | 5006 |
| Beacon (dashboard) | 5050 |

Port 5000 is intentionally avoided — macOS uses it for AirPlay Receiver.

---

## Repository layout

```
camplux/
├── launcher.py          ← Beacon: starts modules + serves dashboard (:5050)
├── run.py               ← bootstrapper: venv + deps, then launcher
├── start.command        ← macOS/Linux double-click wrapper
├── start.bat            ← Windows double-click wrapper
├── requirements.txt     ← Beacon deps (flask, requests)
├── templates/index.html ← dashboard UI
├── vault/    🐋  app.py · db.py · scrapers/ · templates/
├── quarry/   🦊  app.py · local_db.py · scrapers/ · templates/
├── cleaner/  🐱  app.py · yene_io.py · templates/
├── prism/    🐍  app.py · llm.py · prompts.py · questions/ · templates/
├── weaver/   🕷️  app.py · network.py · yene_io.py · templates/
└── stats/    🦅  app.py · yene_io.py · templates/
```

Each module is a self-contained Flask app — you can `cd` into any folder and
run `python app.py` to use it standalone, independent of Beacon.

---

## History & provenance

CAMPlux was migrated from a git-submodule prototype into this single clean
monorepo on 2026-06-24. The prototype modules remain archived under the
`heelgueta` GitHub account (CulpemCorpus, YeneConservatio, LlallinRelatio,
ÑarkiMundatio, MañkeAnalytica, FiluSententia) and under the
`MolfunCognitio`/`KullinCognitio` umbrella as a frozen backup. This repo is the
canonical, citable version going forward.

---

## License & citation

Part of the LAMP UMAG research tooling ecosystem. For academic use; please cite
the lab when CAMPlux contributes to published work.
