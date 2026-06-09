"""
search_multimodal.py
Demuestra búsqueda multimodal con CLIP:
  - Texto → Imagen: la query de texto se embebe con CLIP y busca imágenes similares
  - Imagen → Imagen: una imagen de consulta busca imágenes visualmente similares

Requiere que el índice 'multimedia_vector_index' en Atlas esté en estado READY.
"""

import os
import sys
import time
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from PIL import Image

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

MONGO_URI  = os.getenv("MONGO_URI")
DB_NAME    = os.getenv("DB_NAME", "agencia_viajes_rag")
CLIP_MODEL = "clip-ViT-B-32"
TOP_K      = 5


def wait_index_ready(collection, index_name: str, max_wait: int = 120):
    print(f"Esperando índice '{index_name}'...", end="", flush=True)
    for _ in range(max_wait // 5):
        indexes = list(collection.list_search_indexes())
        for idx in indexes:
            if idx["name"] == index_name:
                status = idx.get("status", "UNKNOWN")
                if status == "READY":
                    print(f" READY ✓")
                    return True
                print(f" {status}...", end="", flush=True)
                break
        time.sleep(5)
    print(" TIMEOUT — puede que el índice aún no esté listo")
    return False


def text_to_image_search(query_text: str, model, collection,
                          categoria: str = None, top_k: int = TOP_K) -> list[dict]:
    """Embebe el texto con CLIP y busca las imágenes más similares."""
    vec = model.encode([query_text])[0].tolist()

    filter_doc = {}
    if categoria:
        filter_doc["categoria"] = {"$eq": categoria}

    pipeline = [
        {
            "$vectorSearch": {
                "index": "multimedia_vector_index",
                "path": "embedding",
                "queryVector": vec,
                "numCandidates": top_k * 15,
                "limit": top_k,
                **({"filter": filter_doc} if filter_doc else {}),
            }
        },
        {
            "$project": {
                "_id": 0,
                "doc_id": 1,
                "titulo_fuente": 1,
                "categoria": 1,
                "nombre_archivo": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    return list(collection.aggregate(pipeline))


def image_to_image_search(query_img_path: str, model, collection,
                           top_k: int = TOP_K) -> list[dict]:
    """Embebe la imagen de consulta con CLIP y busca imágenes visualmente similares."""
    img = Image.open(query_img_path).convert("RGB")
    vec = model.encode([img])[0].tolist()

    query_doc_id = os.path.basename(query_img_path).replace(".png", "")

    pipeline = [
        {
            "$vectorSearch": {
                "index": "multimedia_vector_index",
                "path": "embedding",
                "queryVector": vec,
                "numCandidates": top_k * 15 + 1,
                "limit": top_k + 1,  # +1 para excluir la imagen de consulta
            }
        },
        {
            "$project": {
                "_id": 0,
                "doc_id": 1,
                "titulo_fuente": 1,
                "categoria": 1,
                "nombre_archivo": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    results = list(collection.aggregate(pipeline))
    # Excluir la imagen de consulta de los resultados
    return [r for r in results if r["doc_id"] != query_doc_id][:top_k]


def print_results(results: list[dict], query: str, mode: str):
    print(f"\n{'─'*60}")
    print(f"  Modo: {mode}")
    print(f"  Query: \"{query}\"")
    print(f"{'─'*60}")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['score']:.4f}] {r['doc_id']:12s} | {r['categoria']:12s} | {r['titulo_fuente']}")
    if not results:
        print("  (sin resultados — ¿índice listo?)")


def main():
    print("=" * 60)
    print("  BÚSQUEDA MULTIMODAL CLIP — Agencia de Viajes Colombia")
    print("=" * 60)

    print(f"\nCargando CLIP '{CLIP_MODEL}'...")
    model = SentenceTransformer(CLIP_MODEL)

    client = MongoClient(MONGO_URI)
    col    = client[DB_NAME]["multimedia"]

    # Verificar estado del índice
    ready = wait_index_ready(col, "multimedia_vector_index", max_wait=120)
    if not ready:
        print("\nEjecutando de todas formas — puede haber resultados vacíos si el índice no está listo.")

    # ── BLOQUE 1: Texto → Imagen ──────────────────────────────────────────────
    print("\n\n╔══════════════════════════════════════════════════════════╗")
    print("║          TEXTO → IMAGEN (6 consultas)                    ║")
    print("╚══════════════════════════════════════════════════════════╝")

    text_queries = [
        ("playas tropicales y aguas turquesas en el Caribe", None),
        ("selva amazónica con biodiversidad tropical", None),
        ("ciudad moderna con arquitectura urbana", None),
        ("desierto árido con dunas y paisaje seco", None),
        ("montañas andinas con niebla y vegetación", None),
        ("paquetes de playa todo incluido", "paquetes"),
    ]

    for q_text, categoria in text_queries:
        results = text_to_image_search(q_text, model, col, categoria=categoria)
        label = f"texto→imagen{'  [cat: '+categoria+']' if categoria else ''}"
        print_results(results, q_text, label)

    # ── BLOQUE 2: Imagen → Imagen ─────────────────────────────────────────────
    print("\n\n╔══════════════════════════════════════════════════════════╗")
    print("║          IMAGEN → IMAGEN (4 consultas)                   ║")
    print("╚══════════════════════════════════════════════════════════╝")

    BASE_IMG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "imagenes")
    img_queries = [
        (os.path.join(BASE_IMG, "destinos", "dest_001.png"), "dest_001 (Cartagena)"),
        (os.path.join(BASE_IMG, "destinos", "dest_006.png"), "dest_006 (Amazonía)"),
        (os.path.join(BASE_IMG, "paquetes",  "paq_003.png"), "paq_003 (Eje Cafetero Aventura)"),
        (os.path.join(BASE_IMG, "destinos", "dest_012.png"), "dest_012 (Tatacoa)"),
    ]

    for img_path, label in img_queries:
        if not os.path.exists(img_path):
            print(f"  AVISO: imagen no encontrada — {img_path}")
            continue
        results = image_to_image_search(img_path, model, col)
        print_results(results, label, "imagen→imagen")

    client.close()
    print("\n" + "=" * 60)
    print("  Búsqueda multimodal completada.")
    print("=" * 60)


if __name__ == "__main__":
    main()
