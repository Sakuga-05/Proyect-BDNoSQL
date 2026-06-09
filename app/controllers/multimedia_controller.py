from app.schemas.multimedia import MultimediaSearchRequest, MultimediaSearchResponse
from app.services.multimedia_service import MultimediaService


class MultimediaController:
    def __init__(self, service: MultimediaService) -> None:
        self._service = service

    async def search(self, request: MultimediaSearchRequest) -> MultimediaSearchResponse:
        return await self._service.search(request)
