from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.database import get_database
from app.config.settings import Settings, get_settings
from app.controllers.chunking_controller import ChunkingController
from app.controllers.multimedia_controller import MultimediaController
from app.controllers.multimedia_clip_controller import MultimediaClipController
from app.controllers.multimodal_controller import MultimodalController
from app.controllers.rag_controller import RagController
from app.controllers.search_controller import SearchController
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.multimedia_clip_repository import MultimediaClipRepository
from app.repositories.multimedia_repository import MultimediaRepository
from app.repositories.rag_query_repository import RagQueryRepository
from app.services.chunk_ingestion_service import ChunkIngestionService
from app.services.chunking_service import ChunkingService
from app.services.clip_embedding_service import ClipEmbeddingService
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.services.multimedia_clip_service import MultimediaClipService
from app.services.multimedia_service import MultimediaService
from app.services.rag_service import RagService
from app.services.vector_search_service import VectorSearchService

_embedding_service: EmbeddingService | None = None
_clip_embedding_service: ClipEmbeddingService | None = None


def get_embedding_service(settings: Settings = Depends(get_settings)) -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(settings)
    return _embedding_service


def get_clip_embedding_service(settings: Settings = Depends(get_settings)) -> ClipEmbeddingService:
    global _clip_embedding_service
    if _clip_embedding_service is None:
        _clip_embedding_service = ClipEmbeddingService(settings)
    return _clip_embedding_service


def get_chunk_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> ChunkRepository:
    return ChunkRepository(db)


def get_multimedia_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> MultimediaRepository:
    return MultimediaRepository(db)


def get_multimedia_clip_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> MultimediaClipRepository:
    return MultimediaClipRepository(db)


def get_rag_query_repository(db: AsyncIOMotorDatabase = Depends(get_database)) -> RagQueryRepository:
    return RagQueryRepository(db)


def get_vector_search_service(
    settings: Settings = Depends(get_settings),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
) -> VectorSearchService:
    return VectorSearchService(settings, embedding_service, chunk_repository)


def get_gemini_service(settings: Settings = Depends(get_settings)) -> GeminiService:
    return GeminiService(settings)


def get_rag_service(
    vector_search_service: VectorSearchService = Depends(get_vector_search_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    rag_query_repository: RagQueryRepository = Depends(get_rag_query_repository),
) -> RagService:
    return RagService(vector_search_service, gemini_service, rag_query_repository)


def get_multimedia_service(
    settings: Settings = Depends(get_settings),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    multimedia_repository: MultimediaRepository = Depends(get_multimedia_repository),
) -> MultimediaService:
    return MultimediaService(settings, embedding_service, multimedia_repository)


def get_multimedia_clip_service(
    settings: Settings = Depends(get_settings),
    embedding_service: ClipEmbeddingService = Depends(get_clip_embedding_service),
    multimedia_clip_repository: MultimediaClipRepository = Depends(get_multimedia_clip_repository),
) -> MultimediaClipService:
    return MultimediaClipService(settings, embedding_service, multimedia_clip_repository)


def get_chunk_ingestion_service(
    settings: Settings = Depends(get_settings),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
) -> ChunkIngestionService:
    return ChunkIngestionService(
        settings=settings,
        chunking_service=ChunkingService(settings),
        embedding_service=embedding_service,
        chunk_repository=chunk_repository,
    )


def get_search_controller(
    service: VectorSearchService = Depends(get_vector_search_service),
) -> SearchController:
    return SearchController(service)


def get_rag_controller(service: RagService = Depends(get_rag_service)) -> RagController:
    return RagController(service)


def get_multimedia_controller(
    service: MultimediaService = Depends(get_multimedia_service),
) -> MultimediaController:
    return MultimediaController(service)


def get_multimedia_clip_controller(
    service: MultimediaClipService = Depends(get_multimedia_clip_service),
) -> MultimediaClipController:
    return MultimediaClipController(service)


def get_multimodal_controller(
    service: MultimediaClipService = Depends(get_multimedia_clip_service),
) -> MultimodalController:
    return MultimodalController(service)


def get_chunking_controller(
    service: ChunkIngestionService = Depends(get_chunk_ingestion_service),
) -> ChunkingController:
    return ChunkingController(service)
