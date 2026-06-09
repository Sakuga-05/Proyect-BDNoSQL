# app/scripts/load_destinations.py
import asyncio

from app.config.database import mongo
from app.repositories.destino_repository import DestinoRepository
from app.utils.helpers import utc_now

DESTINOS = [
    {
        "nombre": "Cartagena",
        "pais": "Colombia",
        "ciudad": "Cartagena",
        "descripcion": "Destino historico y de playa en el Caribe colombiano.",
        "categoria": "playa",
        "tags": ["caribe", "historia", "playa"],
        "creado_en": utc_now(),
    },
    {
        "nombre": "Eje Cafetero",
        "pais": "Colombia",
        "descripcion": "Region cafetera con naturaleza, cultura y parques tematicos.",
        "categoria": "naturaleza",
        "tags": ["cafe", "familia", "naturaleza"],
        "creado_en": utc_now(),
    },
]


async def main() -> None:
    await mongo.connect()
    repository = DestinoRepository(mongo.database)
    await repository.insert_many(DESTINOS)
    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
