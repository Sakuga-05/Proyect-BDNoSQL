# app/scripts/create_indexes.py

import asyncio

from pymongo import ASCENDING, DESCENDING
from pymongo.operations import SearchIndexModel

from app.config.database import mongo
from app.config.settings import get_settings
from app.utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def search_index_exists(collection, index_name: str) -> bool:
    try:
        indexes = await collection.list_search_indexes().to_list(None)

        return any(
            index.get("name") == index_name
            for index in indexes
        )

    except Exception:
        return False


async def main() -> None:

    settings = get_settings()

    logger.info("Iniciando conexión al clúster de MongoDB...")

    await mongo.connect()

    db = mongo.database

    # ==========================================================
    # ÍNDICES TRADICIONALES
    # ==========================================================

    logger.info("Configurando índices tradicionales...")

    try:

        await db.destino.create_index(
            [("categoria", ASCENDING)],
            name="idx_categoria"
        )

        await db.destino.create_index(
            [("nombre", ASCENDING)],
            unique=True,
            name="idx_nombre_unico"
        )

        logger.info("✓ Índices en destino")

        await db.paqueteTuristico.create_index(
            [("destino_id", ASCENDING)],
            name="idx_paquete_destino"
        )

        await db.paqueteTuristico.create_index(
            [("tipo", ASCENDING), ("precio", ASCENDING)],
            name="idx_paquete_tipo_precio"
        )

        logger.info("✓ Índices en paqueteTuristico")

        await db.resena.create_index(
            [("paquete_id", ASCENDING), ("creado_en", DESCENDING)],
            name="idx_resena_paquete_fecha"
        )

        logger.info("✓ Índices en resena")

        await db.multimedia.create_index(
            [("destino_id", ASCENDING)],
            name="idx_multimedia_destino"
        )

        logger.info("✓ Índices en multimedia")

        await db.multimedia_clip.create_index(
            [("destino_id", ASCENDING)],
            name="idx_clip_destino"
        )

        await db.multimedia_clip.create_index(
            [("nombre_destino", ASCENDING)],
            name="idx_clip_nombre_destino"
        )

        logger.info("✓ Índices en multimedia_clip")

    except Exception as exc:
        logger.warning("Error creando índices tradicionales: %s", exc)

    # ==========================================================
    # VECTOR SEARCH
    # ==========================================================

    logger.info("Configurando índices vectoriales...")

    chunks_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": settings.embedding_dim,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "doc_id"},
            {"type": "filter", "path": "estrategia_chunking"},
            {"type": "filter", "path": "modelo"},
        ]
    }

    multimedia_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": settings.embedding_dim,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "tipo"},
            {"type": "filter", "path": "destino_id"},
            {"type": "filter", "path": "paquete_id"},
        ]
    }

    multimedia_clip_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": settings.clip_embedding_dim,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "destino_id"},
            {"type": "filter", "path": "nombre_destino"},
        ]
    }

    index_configs = [

        (
            "chunks",
            settings.mongodb_vector_index,
            chunks_definition
        ),

        (
            "multimedia",
            settings.mongodb_multimedia_vector_index,
            multimedia_definition
        ),

        (
            "multimedia_clip",
            settings.mongodb_multimedia_clip_vector_index,
            multimedia_clip_definition
        ),
    ]

    for collection_name, index_name, definition in index_configs:

        collection = db[collection_name]

        try:

            exists = await search_index_exists(
                collection,
                index_name
            )

            if exists:

                logger.info(
                    "✓ Índice '%s' ya existe en '%s'",
                    index_name,
                    collection_name,
                )

                continue

            await collection.create_search_index(
                model=SearchIndexModel(
                    definition=definition,
                    name=index_name,
                    type="vectorSearch",
                )
            )

            logger.info(
                "✓ Índice vectorial '%s' creado en '%s'",
                index_name,
                collection_name,
            )

        except Exception as exc:

            logger.warning(
                "No se pudo crear '%s' en '%s': %s",
                index_name,
                collection_name,
                exc,
            )

    logger.info("--- CONFIGURACIÓN FINALIZADA ---")

    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())