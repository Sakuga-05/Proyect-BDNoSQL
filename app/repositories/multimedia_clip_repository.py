from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.collections import MULTIMEDIA_CLIP_COLLECTION
from app.repositories.base_repository import BaseRepository


class MultimediaClipRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, MULTIMEDIA_CLIP_COLLECTION)

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
                        "destino_id": 1,
                        "nombre_destino": 1,
                        "url": 1,
                        "descripcion_visual": 1,
                        "modelo": 1,
                        "fecha_ingesta": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]
        )
