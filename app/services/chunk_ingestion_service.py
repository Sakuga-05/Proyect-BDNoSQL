#app/services/chunk_ingestion_service.py
from app.config.settings import Settings
from app.models.chunk import ChunkingStrategy
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.chunking import ChunkPreview, ChunkingCompareRequest, ChunkingCompareResponse
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.utils.helpers import utc_now


class ChunkIngestionService:
    def __init__(
        self,
        settings: Settings,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        chunk_repository: ChunkRepository,
    ) -> None:
        self._settings = settings
        self._chunking_service = chunking_service
        self._embedding_service = embedding_service
        self._chunk_repository = chunk_repository

    async def compare(self, request: ChunkingCompareRequest) -> ChunkingCompareResponse:
        chunks_by_strategy = self._chunking_service.compare(request.text, request.strategies)
        stats = [
            self._chunking_service.stats(strategy, chunks)
            for strategy, chunks in chunks_by_strategy.items()
        ]
        previews = [
            ChunkPreview(
                chunk_index=index,
                estrategia_chunking=strategy,
                chunk_texto=chunk,
                caracteres=len(chunk),
            )
            for strategy, chunks in chunks_by_strategy.items()
            for index, chunk in enumerate(chunks)
        ]

        if request.persist:
            await self._persist_chunks(request.doc_id, chunks_by_strategy)

        return ChunkingCompareResponse(
            doc_id=request.doc_id,
            persisted=request.persist,
            stats=stats,
            previews=previews[:20],
        )

    async def _persist_chunks(
        self,
        doc_id: str,
        chunks_by_strategy: dict[ChunkingStrategy, list[str]],
    ) -> None:
        documents = []
        for strategy, chunks in chunks_by_strategy.items():
            embeddings = await self._embedding_service.embed_texts(chunks)
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                documents.append(
                    {
                        "doc_id": doc_id,
                        "chunk_index": index,
                        "estrategia_chunking": strategy,
                        "chunk_texto": chunk,
                        "embedding": embedding,
                        "modelo": self._settings.embedding_model,
                        "fecha_ingesta": utc_now(),
                    }
                )
        await self._chunk_repository.insert_many(documents)
