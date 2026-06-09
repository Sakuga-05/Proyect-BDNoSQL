from fastapi import APIRouter, Depends, status

from app.config.dependencies import get_search_controller
from app.controllers.search_controller import SearchController
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search(
    request: SearchRequest,
    controller: SearchController = Depends(get_search_controller),
) -> SearchResponse:
    return await controller.search(request)
