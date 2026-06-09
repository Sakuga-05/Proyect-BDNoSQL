#services/vector_search_service.py
from typing import Any

from app.config.settings import Settings
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.embedding_service import EmbeddingService


class VectorSearchService:
    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        chunk_repository: ChunkRepository,
    ) -> None:
        self._settings = settings
        self._embedding_service = embedding_service
        self._chunk_repository = chunk_repository

    async def search(self, request: SearchRequest) -> SearchResponse:
        query_vector = await self._embedding_service.embed_text(request.query)
        filters = self._build_filters(request.estrategia_chunking, request.filters)
        raw_results = await self._chunk_repository.vector_search(
            query_vector=query_vector,
            index_name=self._settings.mongodb_vector_index,
            limit=request.limit,
            num_candidates=self._settings.vector_num_candidates,
            filters=filters,
        )
        results = [
            SearchResult(
                id=document.get("_id"),
                doc_id=document.get("doc_id"),
                score=document.get("score"),
                texto=document.get("chunk_texto", ""),
                metadata={
                    "chunk_index": document.get("chunk_index"),
                    "estrategia_chunking": document.get("estrategia_chunking"),
                    "modelo": document.get("modelo"),
                    **(document.get("metadata") or {}),
                },
            )
            for document in raw_results
        ]
        return SearchResponse(query=request.query, total=len(results), results=results)

    @staticmethod
    def _build_filters(strategy: str | None, filters: dict[str, Any]) -> dict[str, Any]:
        built = dict(filters)
        if strategy:
            built["estrategia_chunking"] = strategy
        return built
