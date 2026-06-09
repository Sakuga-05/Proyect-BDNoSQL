import asyncio
from pymongo import ASCENDING, DESCENDING

from app.config.database import mongo
from app.config.settings import get_settings
from app.utils.logger import configure_logging, get_logger

# Configuración inicial del logger para trazar el despliegue de infraestructura
configure_logging()
logger = get_logger(__name__)


async def main() -> None:
    settings = get_settings()
    
    logger.info("Iniciando conexión al clúster de MongoDB...")
    await mongo.connect()
    db = mongo.database

    # =========================================================================
    # 1. ÍNDICES TRADICIONALES (B-TREE) PARA CONSULTAS FRECUENTES DE NEGOCIO
    # =========================================================================
    logger.info("Configurando índices tradicionales para optimización de queries...")

    try:
        # Destinos: Búsquedas frecuentes por categoría y ordenamiento alfabético por nombre
        await db.destino.create_index([("categoria", ASCENDING)])
        await db.destino.create_index([("nombre", ASCENDING)], unique=True)
        logger.info("✓ Índices creados en colección 'destino'")

        # Paquetes Turísticos: Filtros combinados por destino, tipo de plan y rango de precios
        await db.paqueteTuristico.create_index([("destino_id", ASCENDING)])
        await db.paqueteTuristico.create_index([("tipo", ASCENDING), ("precio", ASCENDING)])
        logger.info("✓ Índices creados en colección 'paqueteTuristico'")

        # Reseñas: Carga rápida de comentarios asociados a un paquete específico ordenados por fecha
        await db.resena.create_index([("paquete_id", ASCENDING), ("creado_en", DESCENDING)])
        logger.info("✓ Índices creados en colección 'resena'")

        # Multimedia: Búsquedas por ID de destino para pintar galerías de fotos
        await db.multimedia.create_index([("destino_id", ASCENDING)])
        logger.info("✓ Índices creados en colección 'multimedia'")

    except Exception as exc:
        logger.error("Error al crear índices tradicionales: %s", exc)


    # =========================================================================
    # 2. ÍNDICES DE BÚSQUEDA VECTORIAL EN MONGODB ATLAS (VECTOR SEARCH)
    # =========================================================================
    logger.info("Configurando índices vectoriales mediante comandos de administración de Atlas...")

    # Definición estructural para la base de conocimiento del RAG (Colección: chunks)
    chunks_index_payload = {
        "createSearchIndexes": "chunks",
        "indexes": [
            {
                "name": settings.mongodb_vector_index, # Nombre dinámico desde los settings
                "definition": {
                    "fields": [
                        {
                            "type": "vector",
                            "path": "embedding", # Campo que almacena el array flotante
                            "numDimensions": settings.embedding_dim, # Ej: 384 según tu modelo HF
                            "similarity": "cosine" # Métrica angular óptima para semántica
                        },
                        {"type": "filter", "path": "doc_id"}, # Pre-filtrado por documento base
                        {"type": "filter", "path": "estrategia_chunking"}, # Pre-filtrado de algoritmo
                        {"type": "filter", "path": "modelo"} # Pre-filtrado por versión de IA
                    ]
                }
            }
        ]
    }

    # Definición estructural para la colección de Multimedia
    multimedia_index_payload = {
        "createSearchIndexes": "multimedia",
        "indexes": [
            {
                "name": settings.mongodb_multimedia_vector_index,
                "definition": {
                    "fields": [
                        {
                            "type": "vector",
                            "path": "embedding",
                            "numDimensions": settings.embedding_dim,
                            "similarity": "cosine"
                        },
                        {"type": "filter", "path": "tipo"},
                        {"type": "filter", "path": "destino_id"},
                        {"type": "filter", "path": "paquete_id"}
                    ]
                }
            }
        ]
    }

    multimedia_clip_index_payload = {
        "createSearchIndexes": "multimedia_clip",
        "indexes": [
            {
                "name": settings.mongodb_multimedia_clip_vector_index,
                "definition": {
                    "fields": [
                        {
                            "type": "vector",
                            "path": "embedding",
                            "numDimensions": settings.clip_embedding_dim,
                            "similarity": "cosine"
                        },
                        {"type": "filter", "path": "destino_id"},
                        {"type": "filter", "path": "nombre_destino"}
                    ]
                }
            }
        ]
    }

    # Despliegue de Índices Vectoriales mediante comandos de base de datos crudos (db.command)
    for payload, collection_name in [
        (chunks_index_payload, "chunks"),
        (multimedia_index_payload, "multimedia"),
        (multimedia_clip_index_payload, "multimedia_clip"),
    ]:
        try:
            logger.info("Enviando comando Atlas Vector Search para la colección: %s...", collection_name)
            await db.command(payload)
            logger.info("✓ Orden de creación del índice vectorial enviada con éxito para '%s'", collection_name)
        except Exception as exc:
            logger.warning("No se pudo procesar el índice vectorial en '%s': %s", collection_name, exc)
            logger.warning("Verifica que estés usando un clúster M10+ o un entorno compatible con Search Indexes.")

    # Cierre seguro de las conexiones en el pool
    await mongo.close()
    logger.info("--- PROCESO DE CONFIGURACIÓN DE INFRAESTRUCTURA DE DATOS FINALIZADO ---")


if __name__ == "__main__":
    # Ejecución del bucle de eventos asíncronos desde la consola
    asyncio.run(main())