from fastapi import APIRouter, Depends, status

from app.config.dependencies import get_rag_controller
from app.controllers.rag_controller import RagController
from app.schemas.rag import RagRequest, RagResponse

router = APIRouter(tags=["rag"])


@router.post("/rag", response_model=RagResponse, status_code=status.HTTP_200_OK)
async def rag(
    request: RagRequest,
    controller: RagController = Depends(get_rag_controller),
) -> RagResponse:
    return await controller.rag(request)
