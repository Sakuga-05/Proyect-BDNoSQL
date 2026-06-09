# app/services/chunking_service.py
import re
from collections.abc import Iterable

from app.config.settings import Settings
from app.models.chunk import ChunkStats, ChunkingStrategy


class ChunkingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def split(self, text: str, strategy: ChunkingStrategy) -> list[str]:
        cleaned = self._normalize_text(text)
        if strategy == "fixed-size":
            return self._fixed_size(cleaned)
        if strategy == "sentence-aware":
            return self._sentence_aware(cleaned)
        raise ValueError(f"Estrategia no soportada: {strategy}")

    def compare(self, text: str, strategies: Iterable[ChunkingStrategy]) -> dict[ChunkingStrategy, list[str]]:
        return {strategy: self.split(text, strategy) for strategy in strategies}

    def stats(self, strategy: ChunkingStrategy, chunks: list[str]) -> ChunkStats:
        lengths = [len(chunk) for chunk in chunks] or [0]
        return ChunkStats(
            estrategia_chunking=strategy,
            total_chunks=len(chunks),
            promedio_caracteres=sum(lengths) / len(lengths),
            minimo_caracteres=min(lengths),
            maximo_caracteres=max(lengths),
        )

    def _fixed_size(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        step = max(1, self._settings.chunk_size - self._settings.chunk_overlap)

        while start < len(text):
            end = min(len(text), start + self._settings.chunk_size)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start += step
        return chunks

    def _sentence_aware(self, text: str) -> list[str]:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for sentence in sentences:
            projected_len = current_len + len(sentence) + (1 if current else 0)
            if current and projected_len > self._settings.sentence_chunk_max_chars:
                chunks.append(" ".join(current))
                current = [sentence]
                current_len = len(sentence)
            else:
                current.append(sentence)
                current_len = projected_len

        if current:
            chunks.append(" ".join(current))
        return chunks or ([text] if text else [])

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()
