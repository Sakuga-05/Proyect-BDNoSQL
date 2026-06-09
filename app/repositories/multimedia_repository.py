# app/repositories/multimedia_repository.py
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.collections import MULTIMEDIA_COLLECTION
from app.repositories.base_repository import BaseRepository


class MultimediaRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, MULTIMEDIA_COLLECTION)

    async def vector_search(
        self,
        query_vector: list[float],
        index_name: str,
        limit: int,
        num_candidates: int,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        vector_stage: dict[str, Any] = {
            "index": index_name,
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": max(num_candidates, limit),
            "limit": limit,
        }
        if filters:
            vector_stage["filter"] = filters

        return await self.aggregate(
            [
                {"$vectorSearch": vector_stage},
                {
                    "$project": {
                        "_id": 1,
                        "titulo": 1,
                        "descripcion": 1,
                        "descripcion_visual": 1,
                        "tipo": 1,
                        "url": 1,
                        "destino_id": 1,
                        "nombre_destino": 1,
                        "paquete_id": 1,
                        "tags": 1,
                        "metadata": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]
        )
