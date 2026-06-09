import asyncio

from PIL import Image

from app.config.database import mongo
from app.config.settings import get_settings
from app.services.clip_embedding_service import ClipEmbeddingService
from app.utils.helpers import utc_now
from app.utils.multimedia_assets import build_static_url, build_visual_description, iter_destination_images


async def main() -> None:
    settings = get_settings()

    print("Conectando a MongoDB...")
    await mongo.connect()
    db = mongo.database

    print("Eliminando registros anteriores en 'multimedia_clip'...")
    await db.multimedia_clip.delete_many({})

    destinations = await db.destino.find().to_list(None)
    destinations_by_name = {
        str(destination.get("nombre")): destination
        for destination in destinations
        if destination.get("nombre")
    }

    embedding_service = ClipEmbeddingService(settings)
    items = iter_destination_images()
    documents: list[dict[str, object]] = []
    skipped = 0

    for destination_name, image_path in items:
        destino = destinations_by_name.get(destination_name)
        if destino is None:
            skipped += 1
            continue

        with Image.open(image_path) as image_obj:
            image = image_obj.convert("RGB")
            embedding = await embedding_service.embed_image(image)

        documents.append(
            {
                "destino_id": destino["_id"],
                "nombre_destino": destination_name,
                "url": build_static_url(destination_name, image_path),
                "descripcion_visual": build_visual_description(destino, 0),
                "embedding": embedding,
                "modelo": settings.clip_embedding_model,
                "fecha_ingesta": utc_now(),
            }
        )

    if documents:
        print(f"Insertando {len(documents)} documentos en 'multimedia_clip'...")
        await db.multimedia_clip.insert_many(documents)

    print("\n===== ESTADÍSTICAS FINALES =====")
    print(f"Imágenes procesadas: {len(items)}")
    print(f"Documentos insertados: {len(documents)}")
    print(f"Imágenes omitidas sin destino registrado: {skipped}")
    print(f"Registros totales en multimedia_clip: {await db.multimedia_clip.count_documents({})}")

    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
