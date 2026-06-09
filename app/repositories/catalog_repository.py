from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.collections import COLLECTIONS
from app.repositories.base_repository import BaseRepository
from app.utils.exceptions import AppError


class CatalogRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str) -> None:
        if collection_name not in COLLECTIONS:
            raise AppError(f"Coleccion no soportada: {collection_name}")
        super().__init__(db, collection_name)
