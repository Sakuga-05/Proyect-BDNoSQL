from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, GEOSPHERE

from app.config.collections import COLLECTIONS
from app.config.settings import Settings, get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDatabase:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.client: AsyncIOMotorClient | None = None

    async def connect(self) -> None:
        self.client = AsyncIOMotorClient(self._settings.mongo_uri)
        await self.client.admin.command("ping")
        logger.info("Conexion a MongoDB Atlas establecida")

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()
            logger.info("Conexion a MongoDB cerrada")

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self.client is None:
            raise RuntimeError("MongoDB no ha sido inicializado")
        return self.client[self._settings.db_name]

    async def ensure_indexes(self) -> None:
        db = self.database
        existing = await db.list_collection_names()
        for collection_name in COLLECTIONS:
            if collection_name not in existing:
                await db.create_collection(collection_name)

        await db.participante.create_index([("contacto.email", ASCENDING)], unique=True, sparse=True)
        await db.destino.create_index([("ubicacion", GEOSPHERE)], sparse=True)
        await db.paqueteTuristico.create_index([("destino_id", ASCENDING)])
        await db.viajeProgramado.create_index([("paquete_id", ASCENDING), ("fecha_inicio", ASCENDING)])
        await db.chunks.create_index([("doc_id", ASCENDING), ("estrategia_chunking", ASCENDING)])
        await db.chunks.create_index([("modelo", ASCENDING)])
        await db.multimedia.create_index([("tipo", ASCENDING), ("destino_id", ASCENDING)])
        logger.info("Colecciones e indices base verificados")


mongo = MongoDatabase(get_settings())


async def get_database(request: Request) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    database = getattr(request.app.state, "db", None)
    if database is None:
        database = mongo.database
    yield database


async def get_db_from_settings(_: Settings = Depends(get_settings)) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield mongo.database
