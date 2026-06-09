# app/scripts/init_atlas.py
import asyncio

from pymongo.operations import SearchIndexModel

from app.config.database import mongo
from app.config.settings import get_settings
from app.utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def create_vector_indexes() -> None:
    settings = get_settings()
    await mongo.connect()
    await mongo.ensure_indexes()
    db = mongo.database

    chunk_definition = {
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

    for collection_name, index_name, definition in (
        ("chunks", settings.mongodb_vector_index, chunk_definition),
        ("multimedia", settings.mongodb_multimedia_vector_index, multimedia_definition),
    ):
        try:
            await db[collection_name].create_search_index(
                model=SearchIndexModel(definition=definition, name=index_name, type="vectorSearch")
            )
            logger.info("Indice vectorial creado: %s.%s", collection_name, index_name)
        except Exception as exc:
            logger.warning("No se pudo crear %s.%s automaticamente: %s", collection_name, index_name, exc)
            logger.warning("Definicion para Atlas: %s", definition)

    await mongo.close()


if __name__ == "__main__":
    asyncio.run(create_vector_indexes())
