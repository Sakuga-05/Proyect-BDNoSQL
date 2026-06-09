from PIL.Image import Image

from app.schemas.multimedia_clip import MultimediaClipSearchResponse
from app.services.multimedia_clip_service import MultimediaClipService


class MultimediaClipController:
    def __init__(self, service: MultimediaClipService) -> None:
        self._service = service

    async def image_search(self, image: Image, limit: int = 8) -> MultimediaClipSearchResponse:
        return await self._service.search_image(image=image, limit=limit)

    async def text_search(self, query: str, limit: int = 8) -> MultimediaClipSearchResponse:
        return await self._service.search_text(query=query, limit=limit)
