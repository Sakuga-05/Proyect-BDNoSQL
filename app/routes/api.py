from fastapi import APIRouter

from app.routes import (
    catalog_routes,
    chunking_routes,
    multimedia_routes,
    multimodal_routes,
    rag_routes,
    search_routes,
)

api_router = APIRouter()
api_router.include_router(search_routes.router)
api_router.include_router(rag_routes.router)
api_router.include_router(multimedia_routes.router)
api_router.include_router(multimodal_routes.router)
api_router.include_router(chunking_routes.router)
api_router.include_router(catalog_routes.router)
