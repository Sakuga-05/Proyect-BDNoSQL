"""
ingest_multimedia.py
Ingesta multimodal: genera embeddings CLIP (clip-ViT-B-32) para cada imagen
y los almacena en la colección 'multimedia' de MongoDB Atlas.

Cada documento guarda:
  - embedding_imagen (512-dim): del contenido visual de la imagen
  - embedding_texto  (512-dim): del título del documento fuente
Ambos en el mismo espacio CLIP, lo que permite búsqueda cruzada texto↔imagen.
"""

import os
import json
import glob
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from PIL import Image

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("DB_NAME", "agencia_viajes_rag")
BASE_DIR  = os.path.dirname(os.path.dirname(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "data", "imagenes")
DOCS_JSON = os.path.join(BASE_DIR, "data", "documentos.json")
CLIP_MODEL = "clip-ViT-B-32"


def load_clip():
    print(f"Cargando modelo CLIP '{CLIP_MODEL}'...")
    model = SentenceTransformer(CLIP_MODEL)
    print(f"  ✓ Dimensión de embedding: {model.get_embedding_dimension()}")
    return model


def collect_image_paths() -> list[dict]:
    """Recorre data/imagenes/<categoria>/<doc_id>.png y carga metadata desde documentos.json."""
    with open(DOCS_JSON) as f:
        docs = {d["doc_id"]: d for d in json.load(f)}

    items = []
    for path in sorted(glob.glob(os.path.join(IMG_DIR, "**", "*.png"), recursive=True)):
        filename = os.path.basename(path)          # "dest_001.png"
        doc_id   = filename.replace(".png", "")    # "dest_001"
        categoria = os.path.basename(os.path.dirname(path))  # "destinos"

        if doc_id not in docs:
            print(f"  AVISO: {doc_id} no está en documentos.json — omitiendo")
            continue

        doc = docs[doc_id]
        items.append({
            "doc_id":    doc_id,
            "path":      path,
            "filename":  filename,
            "categoria": categoria,
            "titulo":    doc["titulo"],
        })
    return items


def build_mongo_docs(items: list[dict], model: SentenceTransformer) -> list[dict]:
    """Genera embeddings por lotes y construye documentos MongoDB."""
    # Embeddings de imagen (batch)
    print(f"Codificando {len(items)} imágenes con CLIP...")
    images = [Image.open(it["path"]).convert("RGB") for it in items]
    img_embeddings = model.encode(
        images,
        batch_size=16,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    # Embeddings de texto (batch)
    print("Codificando títulos con CLIP...")
    textos = [it["titulo"] for it in items]
    txt_embeddings = model.encode(
        textos,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    now = datetime.now(timezone.utc)
    docs = []
    for i, it in enumerate(items):
        img_size = Image.open(it["path"]).size
        docs.append({
            "doc_id":           it["doc_id"],
            "tipo":             "imagen",
            "nombre_archivo":   it["filename"],
            "ruta_local":       it["path"],
            "categoria":        it["categoria"],
            "titulo_fuente":    it["titulo"],
            # Embedding visual — usado para imagen↔imagen y texto↔imagen
            "embedding":        img_embeddings[i].tolist(),
            # Embedding textual — para consultas de texto contra imágenes
            "embedding_texto":  txt_embeddings[i].tolist(),
            "modelo":           CLIP_MODEL,
            "dim_embedding":    len(img_embeddings[i]),
            "resolucion":       f"{img_size[0]}x{img_size[1]}",
            "fecha_ingesta":    now,
        })
    return docs


def create_search_index(collection):
    """Crea índice vectorial en Atlas para búsqueda texto↔imagen e imagen↔imagen."""
    index_def = {
        "name": "multimedia_vector_index",
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": 512,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "categoria"},
                {"type": "filter", "path": "doc_id"},
                {"type": "filter", "path": "tipo"},
            ]
        },
    }
    try:
        collection.create_search_index(index_def)
        print("  ✓ Índice 'multimedia_vector_index' enviado a Atlas (puede tardar ~60 s en estar READY)")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("  ✓ Índice ya existía — sin cambios")
        else:
            print(f"  AVISO índice: {e}")


def main():
    client = MongoClient(MONGO_URI)
    db     = client[DB_NAME]
    col    = db["multimedia"]

    model = load_clip()
    items = collect_image_paths()
    print(f"\n{len(items)} imágenes encontradas")

    mongo_docs = build_mongo_docs(items, model)

    print(f"\nInsertando {len(mongo_docs)} documentos en 'multimedia'...")
    col.delete_many({})
    result = col.insert_many(mongo_docs)
    print(f"  ✓ {len(result.inserted_ids)} documentos insertados")

    print("\nCreando índice vectorial en Atlas...")
    create_search_index(col)

    # Verificación rápida
    sample = col.find_one({}, {"doc_id": 1, "titulo_fuente": 1, "dim_embedding": 1, "resolucion": 1})
    print(f"\nEjemplo guardado: {sample['doc_id']} | dim={sample['dim_embedding']} | res={sample['resolucion']}")
    print(f"Total en colección: {col.count_documents({})}")

    client.close()
    print("\nIngesta multimodal completada.")


if __name__ == "__main__":
    main()
