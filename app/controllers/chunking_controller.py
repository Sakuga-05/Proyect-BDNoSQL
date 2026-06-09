from app.schemas.chunking import ChunkingCompareRequest, ChunkingCompareResponse
from app.services.chunk_ingestion_service import ChunkIngestionService


class ChunkingController:
    def __init__(self, service: ChunkIngestionService) -> None:
        self._service = service

    async def compare(self, request: ChunkingCompareRequest) -> ChunkingCompareResponse:
        return await self._service.compare(request)
