import math
from PIL.Image import Image

from app.config.settings import Settings
from app.repositories.multimedia_clip_repository import MultimediaClipRepository
from app.schemas.multimedia_clip import (
    MultimediaClipSearchResponse,
    MultimediaClipSearchResult,
)
from app.services.clip_embedding_service import ClipEmbeddingService
from app.utils.helpers import serialize_mongo_value


class MultimediaClipService:
    def __init__(
        self,
        settings: Settings,
        embedding_service: ClipEmbeddingService,
        multimedia_clip_repository: MultimediaClipRepository,
    ) -> None:
        self._settings = settings
        self._embedding_service = embedding_service
        self._multimedia_clip_repository = multimedia_clip_repository

    async def search_image(self, image: Image, limit: int = 8) -> MultimediaClipSearchResponse:
        query_vector = await self._embedding_service.embed_image(image)
        return await self._search_vector(query_vector, query=None, limit=limit)

    async def search_text(self, query: str, limit: int = 8) -> MultimediaClipSearchResponse:
        query_vector = await self._embedding_service.embed_text(query)
        return await self._search_vector(query_vector, query=query, limit=limit)

    async def search_multimodal(
        self,
        query: str | None,
        image: Image | None,
        limit: int = 8,
    ) -> MultimediaClipSearchResponse:
        if not query and image is None:
            raise ValueError("Se requiere query o imagen para la búsqueda multimodal")

        vectors: list[list[float]] = []
        if query:
            vectors.append(await self._embedding_service.embed_text(query))
        if image is not None:
            vectors.append(await self._embedding_service.embed_image(image))

        if len(vectors) == 1:
            query_vector = vectors[0]
        else:
            query_vector = self._normalize_vector(
                [sum(values) / len(vectors) for values in zip(*vectors)]
            )

        return await self._search_vector(query_vector, query=query, limit=limit)

    async def _search_vector(
        self,
        query_vector: list[float],
        query: str | None,
        limit: int,
    ) -> MultimediaClipSearchResponse:
        raw_results = await self._multimedia_clip_repository.vector_search(
            query_vector=query_vector,
            index_name=self._settings.mongodb_multimedia_clip_vector_index,
            limit=limit,
            num_candidates=self._settings.vector_num_candidates,
        )

        return MultimediaClipSearchResponse(
            query=query,
            total=len(raw_results),
            results=[
                MultimediaClipSearchResult(
                    id=serialize_mongo_value(document.get("_id")),
                    url=document.get("url", ""),
                    nombre_destino=document.get("nombre_destino", ""),
                    descripcion_visual=document.get("descripcion_visual"),
                    score=document.get("score"),
                )
                for document in raw_results
            ],
        )

    @staticmethod
    def _normalize_vector(vector: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(float(value) ** 2 for value in vector))
        if magnitude == 0.0:
            return vector
        return [float(value) / magnitude for value in vector]
