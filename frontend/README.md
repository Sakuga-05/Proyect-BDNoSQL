# Frontend Proyect-BDNoSQL

Frontend académico construido con HTML5, CSS3 y JavaScript vanilla para demostrar el backend turístico.

## Requisitos

1. Iniciar el backend:

```bash
uvicorn app.main:app --reload
```

2. Servir el frontend desde la carpeta `frontend`:

```bash
python -m http.server 5500
```

3. Abrir en el navegador:

```text
http://127.0.0.1:5500
```

La URL del backend se configura desde el campo superior de la interfaz. Por defecto usa:

```text
http://127.0.0.1:8000
```

## Vistas

- Inicio: métricas reales de colecciones.
- Destinos: listado de destinos e imágenes asociadas.
- Paquetes: listado con filtros por tipo y precio.
- Texto a texto: búsqueda vectorial sobre chunks.
- Texto a imagen: búsqueda en `multimedia`.
- Imagen a imagen: búsqueda CLIP con archivo local.
- Multimodal: búsqueda con texto e imagen opcional.
- RAG: pregunta, respuesta y fuentes recuperadas.
- Chunking: comparación `fixed-size` y `sentence-aware`.
