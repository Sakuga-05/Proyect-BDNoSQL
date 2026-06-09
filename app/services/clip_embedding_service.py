import math
from functools import cached_property

from anyio import to_thread
from PIL.Image import Image
from sentence_transformers import SentenceTransformer

from app.config.settings import Settings


class ClipEmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @cached_property
    def model(self) -> SentenceTransformer:
        return SentenceTransformer(self._settings.clip_embedding_model)

    async def embed_text(self, text: str) -> list[float]:
        return (await self.embed_texts([text]))[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = await to_thread.run_sync(
            lambda: self.model.encode(texts, normalize_embeddings=True).tolist()
        )
        return embeddings

    async def embed_image(self, image: Image) -> list[float]:
        return (await self.embed_images([image]))[0]

    async def embed_images(self, images: list[Image]) -> list[list[float]]:
        embeddings = await to_thread.run_sync(
            lambda: self.model.encode(images, normalize_embeddings=True).tolist()
        )
        return embeddings
