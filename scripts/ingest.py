"""
ingest.py
Carga los 100 documentos, aplica 3 estrategias de chunking,
genera embeddings y los almacena en MongoDB Atlas (colección chunks_rag).
"""

import os
import json
from datetime import datetime, timezone
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import nltk

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "agencia_viajes_rag")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "documentos.json")


# ── Estrategias de chunking ──────────────────────────────────────────────────

def fixed_chunk(text, chunk_size=220, overlap=40):
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks


def sentence_chunk(text, max_sentences=2):
    sentences = sent_tokenize(text, language="spanish")
    return [
        " ".join(sentences[i:i + max_sentences]).strip()
        for i in range(0, len(sentences), max_sentences)
        if " ".join(sentences[i:i + max_sentences]).strip()
    ]


def semantic_chunk(text, model, threshold=0.45):
    sentences = sent_tokenize(text, language="spanish")
    if len(sentences) <= 1:
        return [s for s in sentences if s.strip()]
    embeddings = model.encode(sentences)
    chunks, current = [], [sentences[0]]
    for i in range(1, len(sentences)):
        sim = cosine_similarity([embeddings[i - 1]], [embeddings[i]])[0][0]
        if sim >= threshold:
            current.append(sentences[i])
        else:
            chunks.append(" ".join(current).strip())
            current = [sentences[i]]
    if current:
        chunks.append(" ".join(current).strip())
    return [c for c in chunks if c]


# ── Pipeline principal ───────────────────────────────────────────────────────

def build_mongo_docs(doc, strategy, chunks, model_name, now):
    records = []
    for idx, texto in enumerate(chunks):
        embedding = None  # se genera en batch más abajo
        records.append({
            "doc_id": doc["doc_id"],
            "chunk_index": idx,
            "estrategia_chunking": strategy,
            "chunk_texto": texto,
            "embedding": embedding,      # relleno después del batch encode
            "modelo": model_name,
            "categoria": doc["categoria"],
            "titulo_fuente": doc["titulo"],
            "fecha_ingesta": now,
            "char_len": len(texto),
            "word_len": len(texto.split()),
        })
    return records


def main():
    print("\n" + "=" * 60)
    print("  Ingesta: chunking + embeddings → MongoDB Atlas")
    print("=" * 60)

    # Cargar documentos
    with open(DATA_FILE, encoding="utf-8") as f:
        documentos = json.load(f)
    print(f"\n✓ {len(documentos)} documentos cargados desde {DATA_FILE}")

    # Cargar modelo
    print(f"  Cargando modelo '{EMBEDDING_MODEL}'...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"  ✓ Modelo listo (dimensión: {model.get_sentence_embedding_dimension()})")

    now = datetime.now(timezone.utc)
    all_records = []

    print("\n  Aplicando chunking a todos los documentos...")
    for doc in documentos:
        text = doc["texto"].strip()
        for strategy, chunks in [
            ("fixed",    fixed_chunk(text)),
            ("sentence", sentence_chunk(text)),
            ("semantic", semantic_chunk(text, model)),
        ]:
            all_records.extend(build_mongo_docs(doc, strategy, chunks, EMBEDDING_MODEL, now))

    print(f"  ✓ {len(all_records)} chunks generados")

    # Generar embeddings en batch
    print("\n  Generando embeddings (esto tarda ~1 min)...")
    textos = [r["chunk_texto"] for r in all_records]
    embeddings = model.encode(textos, batch_size=64, show_progress_bar=True)
    for rec, vec in zip(all_records, embeddings):
        rec["embedding"] = vec.tolist()
    print(f"  ✓ Embeddings generados")

    # Guardar en MongoDB
    print("\n  Conectando a MongoDB Atlas...")
    cliente = MongoClient(MONGO_URI)
    db = cliente[DB_NAME]
    col = db["chunks_rag"]

    col.delete_many({})
    resultado = col.insert_many(all_records)
    cliente.close()

    print(f"  ✓ {len(resultado.inserted_ids)} chunks insertados en '{DB_NAME}.chunks_rag'")

    # Resumen por estrategia
    from collections import defaultdict
    stats = defaultdict(lambda: {"count": 0, "chars": 0})
    for r in all_records:
        s = r["estrategia_chunking"]
        stats[s]["count"] += 1
        stats[s]["chars"] += r["char_len"]

    print("\n  Resumen por estrategia:")
    print(f"  {'Estrategia':<12} {'Chunks':<8} {'Chars prom'}")
    print("  " + "-" * 35)
    for s, v in sorted(stats.items()):
        avg = v["chars"] / v["count"] if v["count"] else 0
        print(f"  {s:<12} {v['count']:<8} {avg:.0f}")

    print("\n✅ Ingesta completada. Chunks listos para búsqueda vectorial.")


if __name__ == "__main__":
    main()
