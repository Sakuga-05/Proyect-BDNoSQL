from app.repositories.rag_query_repository import RagQueryRepository
from app.schemas.rag import RagRequest, RagResponse, RagSource
from app.schemas.search import SearchRequest
from app.services.gemini_service import GeminiService
from app.services.vector_search_service import VectorSearchService
from app.utils.helpers import utc_now


class RagService:
    def __init__(
        self,
        vector_search_service: VectorSearchService,
        gemini_service: GeminiService,
        rag_query_repository: RagQueryRepository,
    ) -> None:
        self._vector_search_service = vector_search_service
        self._gemini_service = gemini_service
        self._rag_query_repository = rag_query_repository

    async def answer(self, request: RagRequest) -> RagResponse:
        search_response = await self._vector_search_service.search(
            SearchRequest(
                query=request.question,
                limit=request.limit,
                estrategia_chunking=request.estrategia_chunking,
                filters=request.filters,
            )
        )
        context = "\n\n".join(
            f"[doc={result.doc_id} score={result.score}] {result.texto}"
            for result in search_response.results
        )
        answer = await self._gemini_service.generate_answer(request.question, context)
        sources = [
            RagSource(
                doc_id=result.doc_id,
                chunk_index=result.metadata.get("chunk_index"),
                score=result.score,
                texto=result.texto,
                metadata=result.metadata,
            )
            for result in search_response.results
        ]
        query_id = await self._rag_query_repository.insert_one(
            {
                "pregunta": request.question,
                "respuesta": answer,
                "chunks_usados": [source.model_dump() for source in sources],
                "modelo_llm": "gemini",
                "fecha_consulta": utc_now(),
            }
        )
        return RagResponse(question=request.question, answer=answer, sources=sources, query_id=query_id)
