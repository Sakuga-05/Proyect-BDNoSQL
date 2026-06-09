#app/repositories/chunk_repository.py
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.collections import VECTOR_COLLECTION
from app.repositories.base_repository import BaseRepository


class ChunkRepository(BaseRepository):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, VECTOR_COLLECTION)

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
                        "doc_id": 1,
                        "chunk_index": 1,
                        "estrategia_chunking": 1,
                        "chunk_texto": 1,
                        "modelo": 1,
                        "metadata": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]
        )
