#app/services/multimedia_service.py
from typing import Any

from app.config.settings import Settings
from app.repositories.multimedia_repository import MultimediaRepository
from app.schemas.multimedia import (
    MultimediaSearchRequest,
    MultimediaSearchResponse,
    MultimediaSearchResult,
)
from app.services.embedding_service import EmbeddingService
from app.utils.helpers import serialize_mongo_value


class MultimediaService:
    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        multimedia_repository: MultimediaRepository,
    ) -> None:
        self._settings = settings
        self._embedding_service = embedding_service
        self._multimedia_repository = multimedia_repository

    async def search(self, request: MultimediaSearchRequest) -> MultimediaSearchResponse:
        query_vector = await self._embedding_service.embed_text(request.query)
        filters = self._build_filters(request)
        raw_results = await self._multimedia_repository.vector_search(
            query_vector=query_vector,
            index_name=self._settings.mongodb_multimedia_vector_index,
            limit=request.limit,
            num_candidates=self._settings.vector_num_candidates,
            filters=filters,
        )
        results = [
            MultimediaSearchResult(
                id=serialize_mongo_value(document.get("_id")),
                titulo=document.get("titulo", ""),
                descripcion=document.get("descripcion") or document.get("descripcion_visual"),
                tipo=document.get("tipo", ""),
                url=document.get("url", ""),
                score=document.get("score"),
                metadata={
                    "destino_id": serialize_mongo_value(document.get("destino_id")),
                    "nombre_destino": serialize_mongo_value(document.get("nombre_destino")),
                    "paquete_id": serialize_mongo_value(document.get("paquete_id")),
                    "tags": serialize_mongo_value(document.get("tags") or []),
                    **serialize_mongo_value(document.get("metadata") or {}),
                },
            )
            for document in raw_results
        ]
        return MultimediaSearchResponse(query=request.query, total=len(results), results=results)

    @staticmethod
    def _build_filters(request: MultimediaSearchRequest) -> dict[str, Any]:
        filters = dict(request.filters)
        if request.tipo:
            filters["tipo"] = request.tipo
        if request.destino_id:
            filters["destino_id"] = request.destino_id
        return filters
