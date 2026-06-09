"""
main.py
API REST del sistema RAG para la agencia de viajes.
Endpoints: POST /search, POST /rag, POST /search/text-to-image, POST /search/image-to-image
"""

import os
import io
import base64
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from PIL import Image
import httpx

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "agencia_viajes_rag")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
CLIP_MODEL = "clip-ViT-B-32"

# Estado global compartido entre requests
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando API RAG...")
    state["mongo"] = MongoClient(MONGO_URI)
    state["db"] = state["mongo"][DB_NAME]
    state["model"] = SentenceTransformer(EMBEDDING_MODEL)
    state["clip"]  = SentenceTransformer(CLIP_MODEL)
    print(f"✓ Modelo RAG '{EMBEDDING_MODEL}' cargado (384 dims)")
    print(f"✓ Modelo CLIP '{CLIP_MODEL}' cargado (512 dims)")
    print(f"✓ Conectado a MongoDB Atlas ({DB_NAME})")
    yield
    state["mongo"].close()


app = FastAPI(
    title="Agencia de Viajes — Sistema RAG",
    description="API para búsqueda vectorial y generación aumentada con recuperación (RAG)",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Modelos de request/response ──────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    estrategia: Optional[str] = None       # "fixed", "sentence", "semantic" o None (todas)
    categoria: Optional[str] = None         # "paquetes", "destinos", "resenas", etc.
    top_k: int = 5

class ChunkResult(BaseModel):
    doc_id: str
    chunk_index: int
    estrategia_chunking: str
    categoria: str
    titulo_fuente: str
    chunk_texto: str
    score: float

class SearchResponse(BaseModel):
    query: str
    resultados: list[ChunkResult]
    total: int

class RagRequest(BaseModel):
    query: str
    estrategia: Optional[str] = None
    categoria: Optional[str] = None
    top_k: int = 5

class RagResponse(BaseModel):
    query: str
    respuesta: str
    fuentes: list[ChunkResult]
    modelo_llm: str
    modelo_embedding: str


# Multimodal
class ImageResult(BaseModel):
    doc_id: str
    titulo_fuente: str
    categoria: str
    nombre_archivo: str
    score: float

class TextToImageRequest(BaseModel):
    query: str
    categoria: Optional[str] = None
    top_k: int = 5

class MultimodalResponse(BaseModel):
    query: str
    modo: str
    resultados: list[ImageResult]
    total: int
    modelo: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def vector_search(query: str, estrategia: Optional[str], categoria: Optional[str], top_k: int) -> list[dict]:
    model: SentenceTransformer = state["model"]
    db = state["db"]

    query_vec = model.encode([query])[0].tolist()

    pipeline_filter = {}
    if estrategia:
        pipeline_filter["estrategia_chunking"] = {"$eq": estrategia}
    if categoria:
        pipeline_filter["categoria"] = {"$eq": categoria}

    vector_stage = {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_vec,
            "numCandidates": top_k * 10,
            "limit": top_k,
        }
    }
    if pipeline_filter:
        vector_stage["$vectorSearch"]["filter"] = pipeline_filter

    pipeline = [
        vector_stage,
        {
            "$project": {
                "_id": 0,
                "doc_id": 1,
                "chunk_index": 1,
                "estrategia_chunking": 1,
                "categoria": 1,
                "titulo_fuente": 1,
                "chunk_texto": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    return list(db["chunks_rag"].aggregate(pipeline))


def clip_search(query_vec: list[float], categoria: Optional[str],
                top_k: int, db, exclude_doc_id: Optional[str] = None) -> list[dict]:
    filter_doc: dict = {}
    if categoria:
        filter_doc["categoria"] = {"$eq": categoria}

    limit = top_k + (1 if exclude_doc_id else 0)
    pipeline: list[dict] = [
        {
            "$vectorSearch": {
                "index": "multimedia_vector_index",
                "path": "embedding",
                "queryVector": query_vec,
                "numCandidates": limit * 15,
                "limit": limit,
                **({"filter": filter_doc} if filter_doc else {}),
            }
        },
        {
            "$project": {
                "_id": 0,
                "doc_id": 1,
                "titulo_fuente": 1,
                "categoria": 1,
                "nombre_archivo": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    results = list(db["multimedia"].aggregate(pipeline))
    if exclude_doc_id:
        results = [r for r in results if r["doc_id"] != exclude_doc_id]
    return results[:top_k]


async def call_groq(query: str, context: str) -> str:
    if not GROQ_API_KEY:
        return "[GROQ_API_KEY no configurada en .env — respuesta LLM no disponible]"

    system_prompt = (
        "Eres un asistente experto de una agencia de viajes colombiana. "
        "Usa ÚNICAMENTE la información del contexto para responder. "
        "Si el contexto no contiene la respuesta, dilo claramente. "
        "Responde siempre en español, de forma clara y útil para el viajero."
    )

    user_message = f"""Contexto recuperado de nuestra base de datos:
---
{context}
---
Pregunta del cliente: {query}"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.3,
                "max_tokens": 512,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Error Groq API: {resp.text}")
    return resp.json()["choices"][0]["message"]["content"].strip()


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "servicio": "Agencia de Viajes RAG API",
        "version": "1.1.0",
        "endpoints": [
            "/search",
            "/rag",
            "/search/text-to-image",
            "/search/image-to-image",
            "/health",
        ],
    }


@app.get("/health")
def health():
    try:
        state["db"].command("ping")
        return {"status": "ok", "mongo": "conectado", "modelo": EMBEDDING_MODEL}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    """
    Búsqueda vectorial pura. Devuelve los top_k chunks más similares a la query.
    Filtra opcionalmente por estrategia_chunking y/o categoría.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="La query no puede estar vacía")

    resultados = vector_search(req.query, req.estrategia, req.categoria, req.top_k)

    chunks = [
        ChunkResult(
            doc_id=r["doc_id"],
            chunk_index=r["chunk_index"],
            estrategia_chunking=r["estrategia_chunking"],
            categoria=r["categoria"],
            titulo_fuente=r["titulo_fuente"],
            chunk_texto=r["chunk_texto"],
            score=round(r["score"], 4),
        )
        for r in resultados
    ]

    return SearchResponse(query=req.query, resultados=chunks, total=len(chunks))


@app.post("/rag", response_model=RagResponse)
async def rag(req: RagRequest):
    """
    Pipeline RAG completo: recuperación vectorial + generación con Groq/Llama 3.1.
    Devuelve la respuesta del LLM y las fuentes usadas como contexto.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="La query no puede estar vacía")

    # 1. Recuperar chunks relevantes
    resultados = vector_search(req.query, req.estrategia, req.categoria, req.top_k)
    if not resultados:
        raise HTTPException(status_code=404, detail="No se encontraron chunks relevantes. Ejecute primero el script de ingesta.")

    # 2. Construir contexto para el LLM
    context_parts = []
    for i, r in enumerate(resultados, 1):
        context_parts.append(
            f"[Fuente {i} — {r['titulo_fuente']} ({r['categoria']})]:\n{r['chunk_texto']}"
        )
    context = "\n\n".join(context_parts)

    # 3. Llamar al LLM
    respuesta = await call_groq(req.query, context)

    chunks = [
        ChunkResult(
            doc_id=r["doc_id"],
            chunk_index=r["chunk_index"],
            estrategia_chunking=r["estrategia_chunking"],
            categoria=r["categoria"],
            titulo_fuente=r["titulo_fuente"],
            chunk_texto=r["chunk_texto"],
            score=round(r["score"], 4),
        )
        for r in resultados
    ]

    return RagResponse(
        query=req.query,
        respuesta=respuesta,
        fuentes=chunks,
        modelo_llm=GROQ_MODEL,
        modelo_embedding=EMBEDDING_MODEL,
    )


@app.post("/search/text-to-image", response_model=MultimodalResponse)
def text_to_image(req: TextToImageRequest):
    """
    Búsqueda multimodal texto→imagen con CLIP.
    La query de texto se embebe con clip-ViT-B-32 y se buscan imágenes similares
    en el espacio semántico compartido del modelo.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="La query no puede estar vacía")

    clip: SentenceTransformer = state["clip"]
    db = state["db"]

    vec = clip.encode([req.query])[0].tolist()
    results = clip_search(vec, req.categoria, req.top_k, db)

    imgs = [
        ImageResult(
            doc_id=r["doc_id"],
            titulo_fuente=r["titulo_fuente"],
            categoria=r["categoria"],
            nombre_archivo=r["nombre_archivo"],
            score=round(r["score"], 4),
        )
        for r in results
    ]
    return MultimodalResponse(
        query=req.query,
        modo="texto→imagen",
        resultados=imgs,
        total=len(imgs),
        modelo=CLIP_MODEL,
    )


@app.post("/search/image-to-image", response_model=MultimodalResponse)
async def image_to_image(
    file: UploadFile = File(...),
    top_k: int = Form(default=5),
    categoria: Optional[str] = Form(default=None),
):
    """
    Búsqueda multimodal imagen→imagen con CLIP.
    Sube una imagen (JPG/PNG) y recupera las más visualmente similares del corpus.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen (JPG/PNG)")

    clip: SentenceTransformer = state["clip"]
    db = state["db"]

    img_bytes = await file.read()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    vec = clip.encode([img])[0].tolist()

    results = clip_search(vec, categoria, top_k, db)

    imgs = [
        ImageResult(
            doc_id=r["doc_id"],
            titulo_fuente=r["titulo_fuente"],
            categoria=r["categoria"],
            nombre_archivo=r["nombre_archivo"],
            score=round(r["score"], 4),
        )
        for r in results
    ]
    return MultimodalResponse(
        query=f"imagen_subida:{file.filename}",
        modo="imagen→imagen",
        resultados=imgs,
        total=len(imgs),
        modelo=CLIP_MODEL,
    )
