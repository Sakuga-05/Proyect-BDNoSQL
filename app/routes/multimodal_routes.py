# app/routes/multimodal_routes.py
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config.dependencies import get_multimodal_controller
from app.controllers.multimodal_controller import MultimodalController
from app.schemas.multimedia_clip import MultimediaClipSearchResponse

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


@router.post("/search", response_model=MultimediaClipSearchResponse, status_code=status.HTTP_200_OK)
async def multimodal_search(
    query: str | None = Form(None),
    file: UploadFile | None = File(None),
    limit: int = Form(8),
    controller: MultimodalController = Depends(get_multimodal_controller),
) -> MultimediaClipSearchResponse:
    """Búsqueda multimodal (imagen + texto opcionales) usando embeddings CLIP.

    - Solo query  → búsqueda texto→imagen
    - Solo file   → búsqueda imagen→imagen
    - Ambos       → embedding promediado y normalizado
    """
    if query is None and file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere al menos un campo 'query' o un archivo 'file'.",
        )

    image = None
    if file is not None:
        try:
            content = await file.read()
            with Image.open(io.BytesIO(content)) as img:
                image = img.convert("RGB")
                image.load()  # Materializar en memoria antes de cerrar el contexto
        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo cargado no es una imagen válida.",
            ) from exc

    return await controller.search(query=query, image=image, limit=limit)