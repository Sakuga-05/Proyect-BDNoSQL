# Agencia de Viajes RAG con FastAPI y MongoDB Atlas

Proyecto base con arquitectura limpia por capas para una agencia de viajes que usa MongoDB Atlas, Atlas Vector Search, embeddings `all-MiniLM-L6-v2` de 384 dimensiones y Gemini Flash mediante `GEMINI_API_KEY`.

## Ejecutar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Configura `.env` tomando como referencia `.env.example`. Para crear colecciones, indices B-tree e intentar crear indices vectoriales en Atlas:

```bash
python -m app.scripts.init_atlas
python -m app.scripts.generate_dataset
python -m app.scripts.create_indexes
python -m app.scripts.generate_embeddings
python -m app.scripts.rebuild_multimedia
python -m app.scripts.generate_clip_embeddings
```

## Endpoints

- `POST /search`: busqueda semantica sobre `chunks`.
- `POST /rag`: recupera contexto desde `chunks`, consulta Gemini y guarda la consulta en `consultas_rag`.
- `POST /multimedia/search`: busqueda semantica sobre la coleccion `multimedia`.
- `POST /chunking/compare`: compara `fixed-size` y `sentence-aware`; si `persist=true`, guarda cada chunk como documento independiente.
- `GET /health`: verificacion basica de la API.

## Colecciones

La app declara y verifica estas colecciones: `participante`, `destino`, `alojamiento`, `transporte`, `proveedor`, `guiaTuristico`, `paqueteTuristico`, `viajeProgramado`, `pago`, `resena`, `seguroViaje`, `multimedia`, `chunks`, `consultas_rag` y `evaluaciones`.

Cada documento de `chunks` persistido por la API incluye:

- `doc_id`
- `chunk_index`
- `estrategia_chunking`
- `chunk_texto`
- `embedding`
- `modelo`
- `fecha_ingesta`

## Archivos Creados

- `app/main.py`: fabrica la aplicacion FastAPI, registra rutas, excepciones y ciclo de vida de MongoDB.
- `app/config/settings.py`: configuracion centralizada con Pydantic Settings v2.
- `app/config/database.py`: cliente Motor async, conexion, cierre y creacion de colecciones e indices base.
- `app/config/collections.py`: nombres oficiales de colecciones.
- `app/config/dependencies.py`: inyeccion de dependencias para repositorios, servicios y controladores.
- `app/models/base.py`: modelos base para documentos Mongo y auditoria.
- `app/models/destino.py`: modelo tipado de destino.
- `app/models/paquete.py`: modelo tipado de paquete turistico.
- `app/models/multimedia.py`: modelo de recursos multimedia con embedding opcional.
- `app/models/chunk.py`: modelo de chunk RAG y estadisticas de chunking.
- `app/models/domain.py`: modelos iniciales para el resto de colecciones del dominio.
- `app/schemas/search.py`: contratos de entrada/salida para `/search`.
- `app/schemas/rag.py`: contratos de entrada/salida para `/rag`.
- `app/schemas/multimedia.py`: contratos de entrada/salida para `/multimedia/search`.
- `app/schemas/chunking.py`: contratos de entrada/salida para `/chunking/compare`.
- `app/repositories/base_repository.py`: operaciones comunes sobre MongoDB.
- `app/repositories/chunk_repository.py`: busqueda vectorial en `chunks`.
- `app/repositories/multimedia_repository.py`: busqueda vectorial en `multimedia`.
- `app/repositories/rag_query_repository.py`: persistencia de consultas RAG.
- `app/repositories/catalog_repository.py`: repositorio generico para colecciones declaradas.
- `app/repositories/destino_repository.py`: repositorio especializado para destinos.
- `app/services/embedding_service.py`: carga lazy de `sentence-transformers` y generacion async de embeddings.
- `app/services/chunking_service.py`: estrategias `fixed-size` y `sentence-aware`.
- `app/services/chunk_ingestion_service.py`: compara chunking y persiste chunks con embeddings.
- `app/services/vector_search_service.py`: caso de uso de busqueda semantica.
- `app/services/gemini_service.py`: integracion con Gemini mediante `google-genai`.
- `app/services/rag_service.py`: orquestacion retrieval + generation + auditoria.
- `app/services/multimedia_service.py`: busqueda vectorial de multimedia.
- `app/controllers/*.py`: capa HTTP delgada que delega en servicios.
- `app/routes/*.py`: declaracion de rutas FastAPI.
- `app/utils/logger.py`: logging centralizado.
- `app/utils/helpers.py`: utilidades de fechas y serializacion Mongo.
- `app/utils/exceptions.py`: excepciones de aplicacion y handlers globales.
- `app/scripts/init_atlas.py`: crea colecciones, indices base e indices vectoriales Atlas si el cluster lo permite.
- `app/scripts/load_destinations.py`: carga destinos de ejemplo.
- `app/scripts/generate_embeddings.py`: genera chunks y embeddings de ejemplo.
- `app/scripts/load_images.py`: carga multimedia de ejemplo con embeddings.
- `.env.example`: plantilla segura de variables de entorno.
- `requirements.txt`: dependencias del proyecto FastAPI/RAG y de experimentos existentes.

## Principios de Diseno

- Responsabilidad unica: cada capa tiene una razon clara para cambiar.
- Inversion de dependencias: FastAPI construye servicios y repositorios con `Depends`.
- Repository Pattern: Motor queda encapsulado fuera de controladores y servicios HTTP.
- Service Layer Pattern: reglas de RAG, chunking, embeddings y LLM viven en servicios.
- Configuracion externa: credenciales y modelos se definen por variables de entorno.
