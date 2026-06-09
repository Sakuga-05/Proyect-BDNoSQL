#app/scripts/rebuild_multimedia.py
import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.config.database import mongo
from app.config.settings import get_settings
from app.services.embedding_service import EmbeddingService
from app.utils.helpers import utc_now
from app.utils.multimedia_assets import build_multimedia_document, iter_destination_images


def build_embedding_text(item: dict[str, Any]) -> str:
    tags = item.get("tags") or []
    fields = [
        str(item.get("descripcion_visual") or item.get("descripcion") or ""),
        str(item.get("nombre_destino") or ""),
        str(item.get("tipo") or ""),
        " ".join(str(tag) for tag in tags),
    ]
    return " ".join(field for field in fields if field).strip()


async def rebuild_multimedia() -> dict[str, int]:
    settings = get_settings()
    embedding_service = EmbeddingService(settings)

    await mongo.connect()
    db = mongo.database

    await db.multimedia.delete_many({})

    destinos = await db.destino.find({}, {"nombre": 1, "descripcion": 1, "categoria": 1, "tags": 1}).to_list(None)
    destinos_por_nombre = {destino["nombre"]: destino for destino in destinos}

    imagenes_por_destino: dict[str, list[Path]] = defaultdict(list)
    for nombre_destino, image_path in iter_destination_images():
        imagenes_por_destino[nombre_destino].append(image_path)

    documents: list[dict[str, Any]] = []
    for nombre_destino, image_paths in imagenes_por_destino.items():
        destino = destinos_por_nombre.get(nombre_destino)
        if destino is None:
            print(f"Destino sin documento en MongoDB, omitido: {nombre_destino}")
            continue
        for index, image_path in enumerate(image_paths, start=1):
            documents.append(build_multimedia_document(destino, image_path, index))

    if documents:
        texts = [build_embedding_text(document) for document in documents]
        embeddings = await embedding_service.embed_texts(texts)
        ingestion_date = utc_now()
        for document, embedding in zip(documents, embeddings, strict=True):
            document["embedding"] = embedding
            document["modelo"] = settings.embedding_model
            document["fecha_ingesta"] = ingestion_date
        await db.multimedia.insert_many(documents)

    await mongo.close()

    return {
        "destinos_procesados": len(imagenes_por_destino),
        "imagenes_encontradas": sum(len(paths) for paths in imagenes_por_destino.values()),
        "registros_multimedia_creados": len(documents),
        "embeddings_generados": len(documents),
    }


async def main() -> None:
    summary = await rebuild_multimedia()
    print("\n===== RESUMEN =====")
    print(f"Destinos procesados: {summary['destinos_procesados']}")
    print(f"Imagenes encontradas: {summary['imagenes_encontradas']}")
    print(f"Registros multimedia creados: {summary['registros_multimedia_creados']}")
    print(f"Embeddings generados: {summary['embeddings_generados']}")


if __name__ == "__main__":
    asyncio.run(main())
