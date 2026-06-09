from fastapi import APIRouter

from app.routes import chunking_routes, multimedia_routes, rag_routes, search_routes

api_router = APIRouter()
api_router.include_router(search_routes.router)
api_router.include_router(rag_routes.router)
api_router.include_router(multimedia_routes.router)
api_router.include_router(chunking_routes.router)
