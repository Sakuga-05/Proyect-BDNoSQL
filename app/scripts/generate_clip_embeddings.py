# app/scripts/generate_clip_embeddings.py
"""
Script para generar embeddings CLIP de todas las imágenes locales
y almacenarlos en la colección multimedia_clip de MongoDB Atlas.

Ejecutar DESPUÉS de:
  1. python -m app.scripts.generate_dataset   (crea destinos en MongoDB)
  2. python -m app.scripts.create_indexes     (crea índice vectorial multimedia_clip_vector_index)

Uso:
  python -m app.scripts.generate_clip_embeddings
"""
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

    # Cargar modelo y verificar dimensión real ANTES de insertar
    embedding_service = ClipEmbeddingService(settings)
    real_dim = embedding_service.embedding_dim
    print(f"Modelo CLIP: {settings.clip_embedding_model}")
    print(f"Dimensión real de embeddings: {real_dim}")
    if real_dim != settings.clip_embedding_dim:
        print(
            f"ADVERTENCIA: settings.clip_embedding_dim={settings.clip_embedding_dim} "
            f"pero el modelo produce {real_dim} dimensiones. "
            f"Actualiza CLIP_EMBEDDING_DIM={real_dim} en tu .env "
            f"Y recrea el índice vectorial con la dimensión correcta."
        )

    print("Eliminando registros anteriores en 'multimedia_clip'...")
    await db.multimedia_clip.delete_many({})

    destinations = await db.destino.find().to_list(None)
    destinations_by_name = {
        str(destination.get("nombre")): destination
        for destination in destinations
        if destination.get("nombre")
    }
    print(f"Destinos en MongoDB: {len(destinations_by_name)}")

    # iter_destination_images() devuelve una lista; guardar en variable para estadísticas
    all_images = iter_destination_images()
    print(f"Imágenes encontradas en disco: {len(all_images)}")

    documents: list[dict[str, object]] = []
    skipped_no_dest = 0
    skipped_error = 0

    for destination_name, image_path in all_images:
        destino = destinations_by_name.get(destination_name)
        if destino is None:
            print(f"  Omitido (sin destino en MongoDB): {destination_name}/{image_path.name}")
            skipped_no_dest += 1
            continue

        try:
            with Image.open(image_path) as image_obj:
                image = image_obj.convert("RGB")
                image.load()  # Materializar en memoria antes de cerrar
            embedding = await embedding_service.embed_image(image)
        except Exception as exc:
            print(f"  Error procesando {image_path}: {exc}")
            skipped_error += 1
            continue

        documents.append(
            {
                "destino_id": destino["_id"],
                "nombre_destino": destination_name,
                "url": build_static_url(destination_name, image_path),
                "descripcion_visual": build_visual_description(destino, len(documents) + 1),
                "embedding": embedding,
                "modelo": settings.clip_embedding_model,
                "embedding_dim": real_dim,
                "fecha_ingesta": utc_now(),
            }
        )

    if documents:
        print(f"\nInsertando {len(documents)} documentos en 'multimedia_clip'...")
        await db.multimedia_clip.insert_many(documents)
    else:
        print("\nNo se insertaron documentos. Verifica que:")
        print("  1. app/static/img/<NombreDestino>/ existan las carpetas")
        print("  2. Los nombres de carpetas coincidan exactamente con 'nombre' en MongoDB")
        print("  3. Los destinos hayan sido insertados (ejecuta generate_dataset.py primero)")

    total_en_db = await db.multimedia_clip.count_documents({})

    print("\n===== ESTADÍSTICAS FINALES =====")
    print(f"Imágenes en disco:            {len(all_images)}")
    print(f"Documentos insertados:        {len(documents)}")
    print(f"Omitidos (sin destino):       {skipped_no_dest}")
    print(f"Omitidos (error PIL):         {skipped_error}")
    print(f"Total en multimedia_clip:     {total_en_db}")
    print(f"Dimensión de embeddings:      {real_dim}")

    if total_en_db > 0:
        sample = await db.multimedia_clip.find_one({"embedding": {"$exists": True}})
        if sample and sample.get("embedding"):
            print(f"Dimensión verificada en DB:   {len(sample['embedding'])}")

    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())