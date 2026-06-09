from functools import cached_property

from anyio import to_thread
from sentence_transformers import SentenceTransformer

from app.config.settings import Settings


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @cached_property
    def model(self) -> SentenceTransformer:
        return SentenceTransformer(self._settings.embedding_model)

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = await to_thread.run_sync(
            lambda: self.model.encode(texts, normalize_embeddings=True).tolist()
        )
        return embeddings
