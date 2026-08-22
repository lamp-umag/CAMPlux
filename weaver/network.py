"""
DewuRelatio — network.py
NLP pipeline: load → clean → (lemmatize) → (detect collocations) → co-occurrence network → GEXF + metadata
"""

import itertools
import json
import re
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ── Stopwords ─────────────────────────────────────────────────────────────────

STOPWORDS = set("""
a al algo algunas algunos ante antes como con contra cual cuando de del
desde donde durante e el ella ellas ellos en entre era erais éramos eran
eras eres es esa esas ese eso esos esta estas este esto estos estoy
estuvo fue fui había habían han has hasta hay haya he hemos hubiera
hubo la las le les lo los mas me mi mía mis mucho mucha muchos muchas
muy más mismo misma no nos nuestro nuestra nuestros nuestras o os otra
otro otras otros para pero poco poca pocos pocas por porque pues que
quien quién se sea sido si sin sobre su sus también te toda todo todos
todas todavía tu tus un una uno unos unas ya yo él así aunque bien cada
casi cerca como cuanto durante entonces entre había hacer hacia hemos
hizo lo mientras mismo mucho nada ni ningún ninguna nos nuestro nunca
otro parte poco puede pues según ser sido sino solo son soy tal también
tanto tenemos tener tiene tienen tienes todo tuvo usted va vamos van
vez voy él están ésta éste estos estás estuvo fueron hubieron tenían
tenía tengo tienen tiene tenia tuve tuvo haya hayan hubo
""".split())

EXTRA_NOISE = {
    "año", "dice", "dijo", "señaló", "indicó", "explicó", "afirmó",
    "destacó", "agregó", "sostuvo", "manifestó", "informó", "comentó",
    "además", "través", "zona", "lugar", "caso", "forma", "tipo",
    "nivel", "punto", "área", "modo", "lado", "fin", "relación",
    "momento", "tiempo", "día", "mes", "semana", "hecho", "persona",
    "foto", "imagen", "video", "fuente", "texto", "artículo",
    "diario", "nota", "redacción", "mismo", "cada", "cuenta",
    "dentro", "fuera", "mientras", "aunque", "porque",
    "decir", "hacer", "tener", "estar", "haber", "poder", "deber",
    "llegar", "pasar", "quedar", "seguir", "partir", "venir", "poner",
}
STOPWORDS |= EXTRA_NOISE

# ── Lazy spaCy model ──────────────────────────────────────────────────────────

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("es_core_news_sm", disable=["ner", "parser", "senter"])
        _nlp.max_length = 5_000_000
    return _nlp


# ── Main pipeline ─────────────────────────────────────────────────────────────

def build(file_paths, settings, output_dir):
    """
    Generator yielding SSE-ready event dicts.

    Event types:
      {"type": "log",      "level": "info|warn|error|ok|dim", "msg": "..."}
      {"type": "progress", "pct": 0-100, "msg": "..."}
      {"type": "done",     "gexf": "...", "meta": "...", "nodes": N, "edges": M}
    """
    min_doc_freq     = int(settings.get("min_doc_freq", 30))
    min_jaccard      = float(settings.get("min_jaccard", 0.12))
    min_word_len     = int(settings.get("min_word_len", 4))
    use_lemma        = settings.get("lemmatization", "1") == "1"
    use_ngrams       = settings.get("ngrams", "1") == "1"
    phrase_min_count = int(settings.get("phrase_min_count", 15))
    phrase_threshold = float(settings.get("phrase_threshold", 8))
    extra_stop       = {
        w.strip().lower()
        for w in settings.get("extra_stopwords", "").split(",")
        if w.strip()
    }

    stopwords = STOPWORDS | extra_stop
    job_id    = uuid.uuid4().hex[:10]
    out_dir   = Path(output_dir)
    out_dir.mkdir(exist_ok=True)

    # ── Load & merge files ────────────────────────────────────────────────────
    yield _log("Cargando archivos…")
    dfs, file_meta = [], []

    for fp in file_paths:
        try:
            df = pd.read_csv(fp, encoding="utf-8-sig")
            dfs.append(df)
            file_meta.append({"name": Path(fp).name, "articles": len(df)})
            yield _log(f"  {Path(fp).name}: {len(df):,} artículos")
        except Exception as e:
            yield _log(f"  Error en {Path(fp).name}: {e}", "warn")

    if not dfs:
        yield _log("Sin archivos válidos. Abortando.", "error")
        return

    df = pd.concat(dfs, ignore_index=True)
    before = len(df)
    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"])
    deduped = before - len(df)
    yield _log(f"  Total: {len(df):,} artículos" +
               (f" ({deduped} duplicados eliminados)" if deduped else ""))

    sources  = sorted(df["source"].dropna().unique().tolist()) if "source" in df.columns else []
    date_min = str(df["date"].min()) if "date" in df.columns else None
    date_max = str(df["date"].max()) if "date" in df.columns else None

    df["full_text"] = (
        df.get("title",     pd.Series(dtype=str)).fillna("") + " " +
        df.get("body_text", pd.Series(dtype=str)).fillna("")
    )

    def clean(text):
        text = text.lower()
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"[^a-záéíóúüñ\s]", " ", text)
        return text

    raw_texts = [clean(t) for t in df["full_text"]]
    total     = len(raw_texts)

    # ── Lemmatize or tokenize ─────────────────────────────────────────────────
    collocations_found = []

    if use_lemma:
        yield _log("Cargando modelo spaCy es_core_news_sm…")
        nlp = _get_nlp()
        yield _log(f"Lemmatizando {total:,} artículos… (puede tardar ~1 min)")

        docs, processed = [], 0
        for doc in nlp.pipe(raw_texts, batch_size=64):
            tokens = [
                t.lemma_.lower() for t in doc
                if len(t.lemma_) >= min_word_len
                and t.lemma_.lower() not in stopwords
                and t.is_alpha
            ]
            docs.append(tokens)
            processed += 1
            if processed % 250 == 0 or processed == total:
                pct = round(processed / total * 100)
                yield {"type": "progress", "pct": pct,
                       "msg": f"  Lemmatizando… {processed:,}/{total:,}"}

        yield _log("  Lemmatización completa.")
    else:
        yield _log("Tokenizando (sin lemmatización)…")
        docs = []
        for text in raw_texts:
            tokens = [
                t for t in text.split()
                if len(t) >= min_word_len and t not in stopwords
            ]
            docs.append(tokens)

    # ── Collocation detection ─────────────────────────────────────────────────
    if use_ngrams:
        from gensim.models.phrases import Phrases
        yield _log("Detectando colocaciones (bigramas → trigramas)…")
        bigram_model  = Phrases(docs, min_count=phrase_min_count, threshold=phrase_threshold)
        bigram_docs   = [bigram_model[doc] for doc in docs]
        trigram_model = Phrases(bigram_docs, min_count=phrase_min_count, threshold=phrase_threshold)
        docs          = [trigram_model[doc] for doc in bigram_docs]

        all_tokens         = [t for doc in docs for t in doc]
        collocations_found = sorted({t for t in all_tokens if "_" in t})
        yield _log(f"  {len(collocations_found)} colocaciones detectadas")
        sample = collocations_found[:12]
        for c in sample:
            yield _log(f"    · {c.replace('_', ' ')}", "dim")
        if len(collocations_found) > 12:
            yield _log(f"    … y {len(collocations_found) - 12} más", "dim")

    # ── Co-occurrence matrix ──────────────────────────────────────────────────
    yield _log("Construyendo matriz de co-ocurrencia…")
    doc_freq: Counter = Counter()
    for doc in docs:
        doc_freq.update(set(doc))

    vocab = {w for w, f in doc_freq.items() if f >= min_doc_freq}
    yield _log(f"  Vocabulario (≥{min_doc_freq} docs): {len(vocab):,} términos")

    edge_raw: Counter = Counter()
    for doc in docs:
        filtered = sorted(set(doc) & vocab)
        for a, b in itertools.combinations(filtered, 2):
            edge_raw[(a, b)] += 1

    edges = []
    for (a, b), w in edge_raw.items():
        j = w / (doc_freq[a] + doc_freq[b] - w)
        if j >= min_jaccard:
            edges.append((a, b, w, round(j, 4)))
    edges.sort(key=lambda x: -x[3])

    active_nodes: set = set()
    for a, b, _, _ in edges:
        active_nodes.add(a)
        active_nodes.add(b)

    yield _log(
        f"  Red: {len(active_nodes):,} nodos · {len(edges):,} aristas "
        f"(Jaccard ≥ {min_jaccard})"
    )

    # ── Write GEXF ────────────────────────────────────────────────────────────
    yield _log("Escribiendo GEXF…")
    gexf_name = f"dewu_{job_id}.gexf"
    meta_name = f"dewu_{job_id}_meta.json"

    root  = ET.Element("gexf", {
        "xmlns": "http://gexf.net/1.3",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://gexf.net/1.3 http://gexf.net/1.3/gexf.xsd",
        "version": "1.3",
    })
    graph = ET.SubElement(root, "graph", defaultedgetype="undirected")

    an = ET.SubElement(graph, "attributes", {"class": "node"})
    ET.SubElement(an, "attribute", {"id": "0", "title": "doc_frequency",  "type": "integer"})
    ET.SubElement(an, "attribute", {"id": "1", "title": "is_collocation", "type": "boolean"})

    ae = ET.SubElement(graph, "attributes", {"class": "edge"})
    ET.SubElement(ae, "attribute", {"id": "0", "title": "jaccard", "type": "float"})

    nodes_el = ET.SubElement(graph, "nodes")
    for node in sorted(active_nodes):
        n  = ET.SubElement(nodes_el, "node", id=node, label=node.replace("_", " "))
        av = ET.SubElement(n, "attvalues")
        ET.SubElement(av, "attvalue", {"for": "0", "value": str(doc_freq[node])})
        ET.SubElement(av, "attvalue", {"for": "1", "value": str("_" in node).lower()})

    edges_el = ET.SubElement(graph, "edges")
    for i, (a, b, raw, jac) in enumerate(edges):
        e  = ET.SubElement(edges_el, "edge",
                           {"id": str(i), "source": a, "target": b, "weight": str(raw)})
        av = ET.SubElement(e, "attvalues")
        ET.SubElement(av, "attvalue", {"for": "0", "value": str(jac)})

    ET.indent(root, space="  ")
    ET.ElementTree(root).write(out_dir / gexf_name, encoding="utf-8", xml_declaration=True)

    # ── Write metadata JSON ───────────────────────────────────────────────────
    meta = {
        "app": "DewuRelatio",
        "suite": "camplux",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "files": file_meta,
            "total_articles": len(df),
            "deduplicated": deduped,
            "sources": sources,
            "date_range": {"from": date_min, "to": date_max},
        },
        "settings": {
            "min_doc_freq": min_doc_freq,
            "min_jaccard": min_jaccard,
            "min_word_len": min_word_len,
            "lemmatization": {
                "enabled": use_lemma,
                "model": "es_core_news_sm" if use_lemma else None,
            },
            "ngrams": {
                "enabled": use_ngrams,
                **( {"phrase_min_count": phrase_min_count,
                     "phrase_threshold": phrase_threshold}
                    if use_ngrams else {} ),
            },
            "extra_stopwords": sorted(extra_stop),
        },
        "processing_notes": {
            "co_occurrence": (
                "Unidad de co-ocurrencia: artículo completo (título + cuerpo). "
                "Dos términos están conectados si aparecen en el mismo artículo."
            ),
            "lemmatization": (
                "Lematización morfológica en español via spaCy es_core_news_sm. "
                "Reduce formas flexionadas a su base léxica "
                "(técnicos→técnico, energías→energía). "
                "Reduce nodos casi-duplicados generados por plurales y género."
                if use_lemma else "Desactivada — tokens sin lematizar."
            ),
            "ngrams": (
                f"Detección de colocaciones via gensim Phrases con puntuación PMI. "
                f"Dos pasadas: bigramas (punta arenas→punta_arenas) y trigramas. "
                f"min_count={phrase_min_count}, threshold={phrase_threshold}. "
                f"{len(collocations_found)} colocaciones detectadas en este corpus."
                if use_ngrams else "Desactivado."
            ),
            "filtering": (
                f"Se excluyen palabras con frecuencia documental < {min_doc_freq}. "
                f"Se excluyen pares con Jaccard < {min_jaccard}. "
                f"Jaccard = co-ocurrencias / (docs_A + docs_B − co-ocurrencias)."
            ),
        },
        "output": {
            "nodes": len(active_nodes),
            "edges": len(edges),
            "collocations_detected": len(collocations_found),
            "collocations_list": [c.replace("_", " ") for c in collocations_found],
            "vocabulary_after_filter": len(vocab),
            "gexf_file": gexf_name,
            "metadata_file": meta_name,
        },
    }

    with open(out_dir / meta_name, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    yield _log(
        f"¡Listo! {len(active_nodes)} nodos · {len(edges)} aristas · "
        f"{len(collocations_found)} colocaciones", "ok"
    )
    yield {
        "type": "done",
        "gexf": gexf_name,
        "meta": meta_name,
        "nodes": len(active_nodes),
        "edges": len(edges),
        "collocations": len(collocations_found),
    }


def _log(msg, level="info"):
    return {"type": "log", "level": level, "msg": msg}
