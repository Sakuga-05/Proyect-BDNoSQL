from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import serialize_many, serialize_mongo, utc_now


class BaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str) -> None:
        self.collection = db[collection_name]

    async def insert_one(self, document: dict[str, Any]) -> str:
        now = utc_now()
        document.setdefault("creado_en", now)
        document.setdefault("actualizado_en", now)
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, documents: list[dict[str, Any]]) -> list[str]:
        if not documents:
            return []
        now = utc_now()
        for document in documents:
            document.setdefault("creado_en", now)
            document.setdefault("actualizado_en", now)
        result = await self.collection.insert_many(documents)
        return [str(inserted_id) for inserted_id in result.inserted_ids]

    async def find_many(self, filters: dict[str, Any], limit: int = 50) -> list[dict[str, Any]]:
        cursor = self.collection.find(filters).limit(limit)
        return serialize_many(await cursor.to_list(length=limit))

    async def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cursor = self.collection.aggregate(pipeline)
        return serialize_many(await cursor.to_list(length=None))

    async def find_one(self, filters: dict[str, Any]) -> dict[str, Any] | None:
        document = await self.collection.find_one(filters)
        return serialize_mongo(document) if document else None
