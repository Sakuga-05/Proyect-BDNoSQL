# app/routes/multimedia_routes.py
from fastapi import APIRouter, Depends, status

from app.config.dependencies import get_multimedia_controller
from app.controllers.multimedia_controller import MultimediaController
from app.schemas.multimedia import MultimediaSearchRequest, MultimediaSearchResponse

router = APIRouter(prefix="/multimedia", tags=["multimedia"])


@router.post("/search", response_model=MultimediaSearchResponse, status_code=status.HTTP_200_OK)
async def multimedia_search(
    request: MultimediaSearchRequest,
    controller: MultimediaController = Depends(get_multimedia_controller),
) -> MultimediaSearchResponse:
    return await controller.search(request)
