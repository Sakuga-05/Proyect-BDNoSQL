"""
init_db.py
Configura MongoDB: crea colecciones con validadores e índices.
Ejecutar UNA SOLA VEZ al inicio del proyecto.
"""

import os
from pymongo import MongoClient, ASCENDING, GEOSPHERE
from pymongo.operations import SearchIndexModel
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))

# Todas las colecciones del proyecto (14 colecciones)
COLECCIONES = [
    "participantes",
    "destinos",
    "alojamientos",
    "transportes",
    "proveedores",
    "guias",
    "paquetes",
    "viajes_programados",
    "pagos",
    "resenas",
    "seguros_viaje",
    "multimedia",
    "chunks_rag",
    "evaluaciones",
]

# ── Validadores JSON Schema ──────────────────────────────────────────────────

VALIDATOR_CHUNKS_RAG = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["doc_id", "chunk_index", "estrategia_chunking", "chunk_texto", "embedding"],
        "properties": {
            "doc_id": {
                "bsonType": "string",
                "description": "Identificador del documento fuente"
            },
            "chunk_index": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Posición del chunk dentro del documento"
            },
            "estrategia_chunking": {
                "bsonType": "string",
                "enum": ["fixed", "sentence", "semantic"],
                "description": "Estrategia usada para dividir el texto"
            },
            "chunk_texto": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Texto del fragmento"
            },
            "embedding": {
                "bsonType": "array",
                "description": "Vector de embeddings de 384 dimensiones"
            },
            "modelo": {
                "bsonType": "string",
                "description": "Nombre del modelo de embeddings"
            },
            "categoria": {
                "bsonType": "string",
                "description": "Categoría temática del documento fuente"
            },
            "fecha_ingesta": {
                "bsonType": "date",
                "description": "Fecha en que se ingresó el chunk"
            }
        }
    }
}

VALIDATOR_VIAJES_PROGRAMADOS = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["paquete_id", "fecha_inicio", "fecha_fin", "cupo_total", "cupo_disponible"],
        "properties": {
            "paquete_id": {
                "bsonType": "objectId",
                "description": "Referencia al paquete turístico"
            },
            "fecha_inicio": {
                "bsonType": "date",
                "description": "Fecha de salida del viaje"
            },
            "fecha_fin": {
                "bsonType": "date",
                "description": "Fecha de regreso del viaje"
            },
            "cupo_total": {
                "bsonType": "int",
                "minimum": 1,
                "description": "Número máximo de participantes"
            },
            "cupo_disponible": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Plazas aún disponibles"
            },
            "estado": {
                "bsonType": "string",
                "enum": ["disponible", "lleno", "cancelado", "finalizado"],
                "description": "Estado actual del viaje"
            },
            "participantes_snapshot": {
                "bsonType": "array",
                "description": "Snapshot desnormalizado de participantes para evitar joins"
            }
        }
    }
}

VALIDATOR_PAQUETES = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["nombre", "destino_principal", "duracion_dias", "precio_base"],
        "properties": {
            "nombre": {"bsonType": "string"},
            "destino_principal": {"bsonType": "string"},
            "duracion_dias": {"bsonType": "int", "minimum": 1},
            "precio_base": {"bsonType": "double", "minimum": 0},
            "incluye": {"bsonType": "array"},
            "categoria": {
                "bsonType": "string",
                "enum": ["playa", "aventura", "cultural", "ecoturismo", "ciudad", "familiar"]
            }
        }
    }
}

# Mapa colección → validador (solo las que tienen validador definido)
VALIDATORS = {
    "chunks_rag": VALIDATOR_CHUNKS_RAG,
    "viajes_programados": VALIDATOR_VIAJES_PROGRAMADOS,
    "paquetes": VALIDATOR_PAQUETES,
}


def conectar():
    cliente = MongoClient(MONGO_URI)
    cliente.admin.command("ping")
    print("✓ Conexión a MongoDB Atlas establecida")
    return cliente


def crear_colecciones(db):
    existentes = db.list_collection_names()
    for nombre in COLECCIONES:
        if nombre not in existentes:
            opciones = {}
            if nombre in VALIDATORS:
                opciones["validator"] = VALIDATORS[nombre]
                opciones["validationLevel"] = "moderate"   # Permite docs existentes
                opciones["validationAction"] = "warn"       # Advierte en lugar de rechazar
            db.create_collection(nombre, **opciones)
            sufijo = " (con validador)" if nombre in VALIDATORS else ""
            print(f"  ✓ Creada: {nombre}{sufijo}")
        else:
            # Si ya existe, actualizar validador si corresponde
            if nombre in VALIDATORS:
                db.command({
                    "collMod": nombre,
                    "validator": VALIDATORS[nombre],
                    "validationLevel": "moderate",
                    "validationAction": "warn"
                })
                print(f"  ↻ Validador actualizado: {nombre}")
            else:
                print(f"  · Ya existe: {nombre}")


def crear_indices_b_tree(db):
    # Participantes: email único
    db.participantes.create_index([("contacto.email", ASCENDING)], unique=True)

    # Destinos: búsqueda geoespacial
    db.destinos.create_index([("ubicacion", GEOSPHERE)])

    # Viajes programados: consultas por paquete y fecha
    db.viajes_programados.create_index([
        ("paquete_id", ASCENDING),
        ("fecha_inicio", ASCENDING)
    ])

    # Chunks: filtros del experimento de chunking
    db.chunks_rag.create_index([("estrategia_chunking", ASCENDING), ("doc_id", ASCENDING)])
    db.chunks_rag.create_index([("categoria", ASCENDING)])

    # Multimedia: búsqueda por documento asociado
    db.multimedia.create_index([("doc_id", ASCENDING), ("tipo", ASCENDING)])

    # Reseñas: por paquete y calificación
    db.resenas.create_index([("paquete_id", ASCENDING), ("calificacion", ASCENDING)])

    print("✓ Índices B-tree creados")


def crear_indice_vectorial(db):
    definicion = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": EMBEDDING_DIM,
                "similarity": "cosine"
            },
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
        print("✓ Índice vectorial creado en Atlas")
    except Exception as e:
        print(f"⚠️  Índice vectorial (crear manualmente en Atlas si falló):")
        print(f"   Colección: chunks_rag | Nombre: vector_index")
        print(f"   {e}")


def main():
    print("\n" + "="*55)
    print("  Configuración de MongoDB — Agencia de Viajes RAG")
    print("="*55)

    cliente = conectar()
    db = cliente[DB_NAME]

    print("\n[1/3] Creando colecciones y validadores...")
    crear_colecciones(db)

    print("\n[2/3] Creando índices B-tree...")
    crear_indices_b_tree(db)

    print("\n[3/3] Creando índice vectorial...")
    crear_indice_vectorial(db)

    print(f"\n✅ Base de datos '{DB_NAME}' configurada con {len(COLECCIONES)} colecciones.")
    cliente.close()


if __name__ == "__main__":
    main()
