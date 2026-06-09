from app.schemas.rag import RagRequest, RagResponse
from app.services.rag_service import RagService


class RagController:
    def __init__(self, service: RagService) -> None:
        self._service = service

    async def rag(self, request: RagRequest) -> RagResponse:
        return await self._service.answer(request)
