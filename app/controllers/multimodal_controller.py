from PIL.Image import Image

from app.schemas.multimedia_clip import MultimediaClipSearchResponse
from app.services.multimedia_clip_service import MultimediaClipService


class MultimodalController:
    def __init__(self, service: MultimediaClipService) -> None:
        self._service = service

    async def search(
        self,
        query: str | None,
        image: Image | None,
        limit: int = 8,
    ) -> MultimediaClipSearchResponse:
        return await self._service.search_multimodal(query=query, image=image, limit=limit)
