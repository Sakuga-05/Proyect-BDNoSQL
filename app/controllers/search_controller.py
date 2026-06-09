from app.schemas.search import SearchRequest, SearchResponse
from app.services.vector_search_service import VectorSearchService


class SearchController:
    def __init__(self, service: VectorSearchService) -> None:
        self._service = service

    async def search(self, request: SearchRequest) -> SearchResponse:
        return await self._service.search(request)
