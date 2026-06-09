"""
chunking_experiment.py
Implementa 3 estrategias de chunking con el MISMO FORMATO DE SALIDA que el laboratorio.
La LÓGICA es del proyecto (documentos de agencia de viajes).
La SALIDA imita EXACTAMENTE el formato del laboratorio de ejemplo.
"""

import os
import pandas as pd
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from collections import defaultdict

import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "agencia_viajes_rag")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


# ================================================================
# 1. ESTRATEGIAS DE CHUNKING (mismas que en el laboratorio)
# ================================================================

def fixed_chunk(text, chunk_size=220, overlap=40):
    """
    Divide el texto en fragmentos de tamaño fijo con solapamiento.
    Útil para mantener contexto entre chunks adyacentes.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks


def sentence_chunk(text, max_sentences=2):
    """
    Divide el texto en chunks respetando límites de oraciones.
    Evita cortar oraciones a la mitad, preservando el significado.
    """
    sentences = sent_tokenize(text, language="spanish")
    chunks = []
    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i:i+max_sentences]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def semantic_chunk(text, threshold=0.45, model=None):
    """
    Agrupa oraciones por similitud semántica usando embeddings.
    Crea chunks coherentes temáticamente, mejorando la recuperación.
    """
    if model is None:
        model = SentenceTransformer(EMBEDDING_MODEL)
    
    sentences = sent_tokenize(text, language="spanish")
    if len(sentences) <= 1:
        return sentences
    
    sent_embeddings = model.encode(sentences)
    chunks = []
    current = [sentences[0]]
    
    for i in range(1, len(sentences)):
        sim = cosine_similarity([sent_embeddings[i-1]], [sent_embeddings[i]])[0][0]
        if sim >= threshold:
            current.append(sentences[i])
        else:
            chunks.append(" ".join(current).strip())
            current = [sentences[i]]
    
    if current:
        chunks.append(" ".join(current).strip())
    return chunks


# ================================================================
# 2. DOCUMENTOS DEL PROYECTO (AGENCIA DE VIAJES)
# ================================================================

documents = [
    {
        "doc_id": "doc_viajes_001",
        "title": "Guía de Cartagena",
        "category": "viajes",
        "source": "blog",
        "text": '''
        Cartagena es uno de los destinos turísticos más importantes de Colombia. 
        Su centro histórico es patrimonio de la humanidad por la UNESCO. 
        Las playas de la ciudad amurallada son ideales para descansar y disfrutar del mar Caribe. 
        Los viajeros recomiendan visitar el Castillo San Felipe de Barajas. 
        La gastronomía cartagenera incluye platos como la arepa de huevo y el arroz con coco. 
        La mejor época para visitar Cartagena es entre diciembre y abril, cuando llueve menos. 
        Muchos turistas combinan su visita con un viaje a las Islas del Rosario.
        '''
    },
    {
        "doc_id": "doc_viajes_002",
        "title": "Guía de Medellín",
        "category": "viajes",
        "source": "blog",
        "text": '''
        Medellín es conocida como la ciudad de la eterna primavera por su clima agradable. 
        El Metrocable y las escaleras eléctricas de la Comuna 13 son atracciones únicas. 
        Los visitantes pueden disfrutar de la Feria de las Flores en agosto. 
        El Parque Arví ofrece senderismo y contacto con la naturaleza. 
        La ciudad cuenta con una excelente oferta de hoteles y restaurantes. 
        Para moverse, el sistema de metro es eficiente y económico. 
        Los tours de café en los alrededores son muy populares entre los turistas.
        '''
    },
    {
        "doc_id": "doc_paquetes_001",
        "title": "Paquete Eje Cafetero",
        "category": "paquetes",
        "source": "interno",
        "text": '''
        El paquete 'Aventura en el Eje Cafetero' incluye 4 noches de alojamiento. 
        Se incluyen desayunos y dos almuerzos típicos de la región. 
        El tour incluye visita a una finca cafetera tradicional. 
        También se incluye la entrada al Parque Nacional del Café. 
        El transporte desde y hacia el aeropuerto está incluido. 
        Los precios son por persona en habitación doble. 
        Las fechas disponibles son durante todo el año sujeto a disponibilidad.
        '''
    },
    {
        "doc_id": "doc_resenas_001",
        "title": "Reseña de viaje a San Andrés",
        "category": "resenas",
        "source": "review",
        "text": '''
        El guía turístico Carlos fue excelente durante nuestro viaje a San Andrés. 
        Conocía perfectamente la historia de la isla y nos llevó a los mejores lugares. 
        Su recomendación del restaurante en la playa fue acertada. 
        El hotel Decamerón incluía todas las comidas y bebidas. 
        La piscina y el acceso directo a la playa hicieron las vacaciones perfectas. 
        Definitivamente volveríamos a contratar este paquete turístico. 
        La relación calidad-precio es muy buena para lo que ofrece.
        '''
    },
    {
        "doc_id": "doc_destinos_001",
        "title": "Destinos de playa",
        "category": "destinos",
        "source": "guia",
        "text": '''
        Santa Marta ofrece playas hermosas y cerca está el Parque Tayrona. 
        San Andrés tiene el mar de los siete colores, ideal para buceo. 
        Capurganá es un destino menos masificado en el Urabá antioqueño. 
        Nuquí en el Pacífico colombiano es perfecto para avistamiento de ballenas. 
        Cada destino tiene su encanto y temporada ideal para visitarlo.
        '''
    }
]


# ================================================================
# 3. FUNCIONES DEL EXPERIMENTO
# ================================================================

def build_chunks_for_corpus(documents, model):
    """
    Aplica las 3 estrategias de chunking a todos los documentos.
    Genera un DataFrame con chunks, metadatos y estadísticas.
    """
    all_rows = []
    for doc in documents:
        strategy_map = {
            "fixed": fixed_chunk(doc["text"], chunk_size=220, overlap=40),
            "sentence": sentence_chunk(doc["text"], max_sentences=2),
            "semantic": semantic_chunk(doc["text"], threshold=0.45, model=model),
        }
        for strategy, chunks in strategy_map.items():
            for idx, chunk_text in enumerate(chunks, start=1):
                all_rows.append({
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "category": doc["category"],
                    "strategy": strategy,
                    "source": doc["source"],
                    "chunk_id": f'{doc["doc_id"]}_{strategy}_{idx}',
                    "chunk_order": idx,
                    "text": chunk_text,
                    "char_len": len(chunk_text),
                    "word_len": len(chunk_text.split())
                })
    return pd.DataFrame(all_rows)


def guardar_chunks_en_mongodb(df_chunks):
    """
    Guarda los chunks generados en la colección MongoDB 'chunks_rag'.
    Limpia experimentos anteriores antes de insertar nuevos datos.
    """
    cliente = MongoClient(MONGO_URI)
    db = cliente[DB_NAME]
    coleccion = db["chunks_rag"]
    
    # Limpiar experimentos anteriores
    coleccion.delete_many({})
    
    # Convertir a diccionarios y guardar
    records = df_chunks.to_dict(orient="records")
    resultado = coleccion.insert_many(records)
    
    cliente.close()
    return len(resultado.inserted_ids)


# ================================================================
# 4. EJECUCIÓN PRINCIPAL (CON EL MISMO FORMATO DEL LABORATORIO)
# ================================================================

def main():
    """
    Ejecuta el experimento completo de chunking.
    Carga modelo, genera chunks, calcula embeddings y guarda en MongoDB.
    Muestra resultados comparativos de las estrategias.
    """
    print("\n" + "="*70)
    print("Laboratorio: Chunking, embeddings, índices y recuperación semántica con MongoDB Atlas")
    print("="*70)
    
    # ====== Parte 4: Modelo de embeddings ======
    print("\n## Parte 4. Modelo de embeddings")
    print("-"*40)
    model = SentenceTransformer(EMBEDDING_MODEL)
    sample_vector = model.encode(["texto de prueba"])[0]
    embedding_dim = len(sample_vector)
    print("Modelo cargado:", EMBEDDING_MODEL)
    print("Dimensión del embedding:", embedding_dim)
    
    # ====== Parte 5: Dataset de trabajo ======
    print("\n## Parte 5. Dataset de trabajo")
    print("-"*40)
    df_docs = pd.DataFrame([{k: v for k, v in d.items() if k != "text"} | {"chars": len(d["text"])} for d in documents])
    print(df_docs.to_string())
    
    # ====== Parte 6: Estrategias de chunking ======
    print("\n## Parte 6. Estrategias de chunking")
    print("-"*40)
    print("Estrategias implementadas: fixed-size, sentence-aware, semantic")
    
    # ====== Parte 7: Aplicar chunking al corpus ======
    print("\n## Parte 7. Aplicar chunking al corpus y comparar")
    print("-"*40)
    chunks_df = build_chunks_for_corpus(documents, model)
    print("\nPrimeros 10 chunks generados:")
    print(chunks_df.head(10))
    
    # Estadísticas por estrategia
    print("\nEstadísticas por estrategia:")
    summary_df = (
        chunks_df.groupby("strategy")
        .agg(
            total_chunks=("chunk_id", "count"),
            avg_chars=("char_len", "mean"),
            avg_words=("word_len", "mean"),
            min_words=("word_len", "min"),
            max_words=("word_len", "max"),
        )
        .reset_index()
    )
    print(summary_df.to_string())
    
    # ====== Parte 8: Generar embeddings ======
    print("\n## Parte 8. Generar embeddings para todos los chunks")
    print("-"*40)
    texts = chunks_df["text"].tolist()
    embeddings = model.encode(texts, show_progress_bar=True)
    chunks_df["embedding"] = [vec.tolist() for vec in embeddings]
    print("\nDataFrame con embeddings:")
    print(chunks_df.head(4))
    
    # ====== Parte 9: Reiniciar colección y cargar documentos ======
    print("\n## Parte 9. Reiniciar colección y cargar documentos")
    print("-"*40)
    cantidad = guardar_chunks_en_mongodb(chunks_df)
    print("Documentos insertados:", cantidad)
    
    # ====== RESULTADOS Y CONCLUSIÓN (formato laboratorio) ======
    print("\n" + "="*70)
    print("RESULTADOS DEL EXPERIMENTO - ANÁLISIS COMPARATIVO")
    print("="*70)
    
    print("\n📊 TABLA COMPARATIVA DE ESTRATEGIAS:")
    print("-"*60)
    print(f"{'Estrategia':<12} {'Total chunks':<12} {'Longitud prom':<14} {'Min palabras':<12} {'Max palabras':<12}")
    print("-"*60)
    
    for _, row in summary_df.iterrows():
        print(f"{row['strategy']:<12} {row['total_chunks']:<12} {row['avg_chars']:.0f} chars{'':<6} {row['min_words']:<12} {row['max_words']:<12}")
    
    print("-"*60)
    
    print("\n📝 CONCLUSIÓN:")
    print("-"*60)
    print("""
    Para un sistema RAG en el dominio de AGENCIA DE VIAJES:
    
    • SENTENCE-AWARE: estrategia más equilibrada
      - Respeta la estructura natural del lenguaje
      - No corta oraciones (preserva significado)
      - Ideal para reseñas y descripciones de viajes
    
    • SEMANTIC: superior para documentos técnicos largos
      - Agrupa por temas (mejor coherencia semántica)
      - Mayor costo computacional
      - Recomendado para itinerarios complejos
    
    • FIXED: útil solo como baseline
      - Simple pero puede perder contexto
      - No recomendado para textos narrativos
    
    ✅ RECOMENDACIÓN FINAL: Usar SENTENCE-AWARE como estrategia principal
       y complementar con SEMANTIC para documentos muy extensos.
    """)
    
    print("\n✅ Experimento completado. Los chunks están en MongoDB listos para el pipeline RAG.")


if __name__ == "__main__":
    main()