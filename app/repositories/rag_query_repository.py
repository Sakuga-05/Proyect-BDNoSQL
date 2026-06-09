from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.collections import RAG_QUERIES_COLLECTION
from app.repositories.base_repository import BaseRepository


class RagQueryRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, RAG_QUERIES_COLLECTION)
