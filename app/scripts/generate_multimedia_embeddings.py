import asyncio
from typing import Any

from app.config.database import mongo
from app.config.settings import get_settings
from app.services.embedding_service import EmbeddingService
from app.utils.helpers import utc_now


def build_embedding_text(item: dict[str, Any], destino: dict[str, Any] | None = None) -> str:
    tags = item.get("tags") or []
    destino_nombre = item.get("nombre_destino") or (destino or {}).get("nombre") or ""
    destino_categoria = (destino or {}).get("categoria") or ""
    fields = [
        str(item.get("descripcion_visual") or item.get("descripcion") or ""),
        str(destino_nombre),
        str(destino_categoria),
        str(item.get("tipo") or ""),
        " ".join(str(tag) for tag in tags),
    ]
    return " ".join(field for field in fields if field).strip()


async def generate_multimedia_embeddings() -> int:
    settings = get_settings()
    await mongo.connect()
    db = mongo.database
    multimedia = await db.multimedia.find().to_list(None)
    embedding_service = EmbeddingService(settings)

    print(f"Multimedia encontrada: {len(multimedia)}")
    generated = 0

    for item in multimedia:
        destino = None
        if item.get("destino_id"):
            destino = await db.destino.find_one({"_id": item["destino_id"]})

        texto_embedding = build_embedding_text(item, destino)
        if not texto_embedding:
            continue

        embedding = await embedding_service.embed_text(texto_embedding)

        await db.multimedia.update_one(
            {"_id": item["_id"]},
            {
                "$set": {
                    "embedding": embedding,
                    "modelo": settings.embedding_model,
                    "fecha_ingesta": utc_now(),
                }
            }
        )
        generated += 1

    await mongo.close()
    print(f"Embeddings multimedia generados: {generated}")
    return generated


async def main() -> None:
    await generate_multimedia_embeddings()


if __name__ == "__main__":
    asyncio.run(main())
