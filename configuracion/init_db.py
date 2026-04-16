"""
init_database.py
Configura MongoDB: crea colecciones e índices.
Ejecutar UNA SOLA VEZ al inicio del proyecto.
"""

import os
from pymongo import MongoClient, ASCENDING, GEOSPHERE
from pymongo.operations import SearchIndexModel
from dotenv import load_dotenv

load_dotenv()

# Configuración desde .env
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))

# Todas las colecciones del proyecto
COLECCIONES = [
    "participantes",    # Clientes
    "destinos",         # Lugares turísticos
    "alojamientos",     # Hoteles, hostales
    "transportes",      # Aviones, buses
    "proveedores",      # Empresas que proveen servicios
    "guias",            # Guías turísticos
    "paquetes",         # Paquetes turísticos
    "viajes_programados", # Fechas específicas de viajes
    "pagos",            # Pagos asociados a reservas
    "resenas",          # Opiniones de viajeros
    "seguros_viaje",    # Pólizas de seguro
    "chunks_rag"        # Fragmentos de texto para búsqueda vectorial
]


def conectar():
    """
    Establece conexión con MongoDB Atlas usando la URI del archivo .env.
    Verifica la conexión con un ping al servidor.
    """
    cliente = MongoClient(MONGO_URI)
    cliente.admin.command('ping')  # Verifica conexión
    return cliente


def crear_colecciones(db):
    """
    Crea todas las colecciones necesarias para el proyecto si no existen.
    MongoDB crea colecciones automáticamente, pero es buena práctica declararlas.
    """
    existentes = db.list_collection_names()
    for nombre in COLECCIONES:
        if nombre not in existentes:
            db.create_collection(nombre)
            print(f"✓ Creada: {nombre}")


def crear_indices_b_tree(db):
    """
    Crea índices B-tree tradicionales para optimizar consultas.
    Incluye índices únicos, geoespaciales y compuestos para búsquedas eficientes.
    """
    # Índice único: evita emails duplicados
    db.participantes.create_index([("contacto.email", ASCENDING)], unique=True)
    
    # Índice geoespacial: permite búsquedas por ubicación (cerca de...)
    db.destinos.create_index([("ubicacion", GEOSPHERE)])
    
    # Índice compuesto: optimiza consultas que filtran por paquete Y fecha
    db.viajes_programados.create_index([
        ("paquete_id", ASCENDING),
        ("fecha_inicio", ASCENDING)
    ])
    
    # Índices para el experimento de chunking
    db.chunks_rag.create_index([("estrategia_chunking", ASCENDING), ("doc_id", ASCENDING)])
    db.chunks_rag.create_index([("categoria", ASCENDING)])
    
    print("✓ Índices B-tree creados")


def crear_indice_vectorial(db):
    """
    Crea índice vectorial para búsqueda semántica en MongoDB Atlas.
    Permite búsquedas por similitud de significado usando embeddings.
    Requiere Atlas; no funciona en MongoDB local.
    """
    definicion = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",           # Campo que contiene el vector
                "numDimensions": EMBEDDING_DIM, # 384 para all-MiniLM-L6-v2
                "similarity": "cosine"         # Métrica de similitud
            },
            # Campos de filtro: restringen búsqueda ANTES de calcular similitud
            {"type": "filter", "path": "estrategia_chunking"},
            {"type": "filter", "path": "categoria"},
            {"type": "filter", "path": "doc_id"}
        ]
    }
    
    try:
        modelo = SearchIndexModel(
            definition=definicion,
            name="vector_index",
            type="vectorSearch"
        )
        db.chunks_rag.create_search_index(model=modelo)
        print("✓ Índice vectorial creado automáticamente")
    except Exception as e:
        # Si falla, mostrar instrucciones para creación manual
        print("⚠️ Crea el índice manualmente en Atlas:")
        print(f"   {definicion}")


def main():
    """
    Función principal que configura completamente la base de datos.
    Crea colecciones, índices B-tree e índice vectorial para el proyecto.
    """
    print("Configurando MongoDB...")
    cliente = conectar()
    db = cliente[DB_NAME]
    
    crear_colecciones(db)
    crear_indices_b_tree(db)
    crear_indice_vectorial(db)
    
    print(f"✅ Listo. Base de datos: {DB_NAME}")
    cliente.close()


if __name__ == "__main__":
    main()