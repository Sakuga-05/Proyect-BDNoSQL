from fastapi import APIRouter, Depends, status

from app.config.dependencies import get_chunking_controller
from app.controllers.chunking_controller import ChunkingController
from app.schemas.chunking import ChunkingCompareRequest, ChunkingCompareResponse

router = APIRouter(prefix="/chunking", tags=["chunking"])


@router.post("/compare", response_model=ChunkingCompareResponse, status_code=status.HTTP_200_OK)
async def compare_chunking(
    request: ChunkingCompareRequest,
    controller: ChunkingController = Depends(get_chunking_controller),
) -> ChunkingCompareResponse:
    return await controller.compare(request)
