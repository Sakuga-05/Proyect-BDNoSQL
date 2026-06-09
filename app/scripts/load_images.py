# app/scripts/load_images.py
import asyncio

from app.config.database import mongo
from app.config.settings import get_settings
from app.repositories.multimedia_repository import MultimediaRepository
from app.services.embedding_service import EmbeddingService
from app.utils.helpers import utc_now

IMAGENES = [
    {
        "titulo": "Murallas de Cartagena",
        "descripcion": "Vista de la ciudad amurallada y el ambiente historico de Cartagena.",
        "tipo": "imagen",
        "url": "https://example.com/cartagena.jpg",
        "destino_id": "cartagena",
        "tags": ["historia", "caribe"],
    },
    {
        "titulo": "Paisaje cafetero",
        "descripcion": "Montanas verdes, cafetales y experiencia rural en el Eje Cafetero.",
        "tipo": "imagen",
        "url": "https://example.com/eje-cafetero.jpg",
        "destino_id": "eje-cafetero",
        "tags": ["cafe", "naturaleza"],
    },
]


async def main() -> None:
    settings = get_settings()
    embedding_service = EmbeddingService(settings)
    await mongo.connect()
    repository = MultimediaRepository(mongo.database)
    documents = []
    for image in IMAGENES:
        searchable_text = f"{image['titulo']}. {image['descripcion']}. {' '.join(image['tags'])}"
        documents.append(
            {
                **image,
                "embedding": await embedding_service.embed_text(searchable_text),
                "modelo": settings.embedding_model,
                "fecha_ingesta": utc_now(),
            }
        )
    await repository.insert_many(documents)
    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
