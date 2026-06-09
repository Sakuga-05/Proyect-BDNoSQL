# app/scripts/generate_embeddings.py

import asyncio

from app.config.database import mongo
from app.config.settings import get_settings
from app.repositories.chunk_repository import ChunkRepository
from app.services.chunk_ingestion_service import ChunkIngestionService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.schemas.chunking import ChunkingCompareRequest


async def main() -> None:
    settings = get_settings()

    print("Conectando a MongoDB...")
    await mongo.connect()

    db = mongo.database

    print("Limpiando colección chunks...")
    await db.chunks.delete_many({})

    service = ChunkIngestionService(
        settings=settings,
        chunking_service=ChunkingService(settings),
        embedding_service=EmbeddingService(settings),
        chunk_repository=ChunkRepository(db),
    )

    paquetes = await db.paqueteTuristico.find().to_list(None)

    print(f"Paquetes encontrados: {len(paquetes)}")

    total_procesados = 0

    for paquete in paquetes:

        texto = f"""
        Título: {paquete.get("titulo", "")}

        Descripción:
        {paquete.get("descripcion", "")}

        Tipo:
        {paquete.get("tipo", "")}

        Duración:
        {paquete.get("duracion_dias", "")} días

        Servicios incluidos:
        {", ".join(paquete.get("servicios_incluidos", []))}

        Precio:
        {paquete.get("precio", "")}
        """

        try:
            await service.compare(
                ChunkingCompareRequest(
                    doc_id=str(paquete["_id"]),
                    text=texto,
                    persist=True,
                )
            )

            total_procesados += 1

            if total_procesados % 10 == 0:
                print(f"Procesados: {total_procesados}")

        except Exception as exc:
            print(
                f"Error procesando paquete "
                f"{paquete.get('titulo', 'SIN_TITULO')}: {exc}"
            )

    print("\n===== RESUMEN =====")
    print(f"Paquetes procesados: {total_procesados}")
    print(
        f"Chunks generados: "
        f"{await db.chunks.count_documents({})}"
    )

    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())