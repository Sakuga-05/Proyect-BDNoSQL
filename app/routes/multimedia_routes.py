# app/routes/multimedia_routes.py
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config.dependencies import (
    get_multimedia_clip_controller,
    get_multimedia_controller,
)
from app.controllers.multimedia_clip_controller import MultimediaClipController
from app.controllers.multimedia_controller import MultimediaController
from app.schemas.multimedia import MultimediaSearchRequest, MultimediaSearchResponse
from app.schemas.multimedia_clip import (
    MultimediaClipSearchResponse,
    MultimediaClipTextSearchRequest,
)

router = APIRouter(prefix="/multimedia", tags=["multimedia"])


@router.post("/search", response_model=MultimediaSearchResponse, status_code=status.HTTP_200_OK)
async def multimedia_search(
    request: MultimediaSearchRequest,
    controller: MultimediaController = Depends(get_multimedia_controller),
) -> MultimediaSearchResponse:
    return await controller.search(request)


@router.post("/image-search", response_model=MultimediaClipSearchResponse, status_code=status.HTTP_200_OK)
async def multimedia_image_search(
    file: UploadFile = File(...),
    limit: int = Form(8),
    controller: MultimediaClipController = Depends(get_multimedia_clip_controller),
) -> MultimediaClipSearchResponse:
    """Búsqueda imagen → imagen usando embeddings CLIP (colección multimedia_clip)."""
    try:
        content = await file.read()
        # Usar contexto de bytes para no dejar el file descriptor abierto
        with Image.open(io.BytesIO(content)) as img:
            image = img.convert("RGB")
            # Forzar carga en memoria antes de cerrar el contexto
            image.load()
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo cargado no es una imagen válida.",
        ) from exc

    return await controller.image_search(image=image, limit=limit)


@router.post(
    "/text-search-clip",
    response_model=MultimediaClipSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def multimedia_text_search_clip(
    request: MultimediaClipTextSearchRequest,
    controller: MultimediaClipController = Depends(get_multimedia_clip_controller),
) -> MultimediaClipSearchResponse:
    """Búsqueda texto → imagen usando embeddings CLIP (colección multimedia_clip)."""
    return await controller.text_search(query=request.query, limit=request.limit)