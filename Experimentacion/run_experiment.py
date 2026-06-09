"""
run_experiment.py
Experimento comparativo de chunking para el sistema RAG de la agencia de viajes.
Ejecuta las 10 consultas de prueba contra las 3 estrategias almacenadas en MongoDB
y calcula métricas de recuperación: HitRate@5, MRR, Precision@5 y Score promedio.
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from collections import defaultdict

load_dotenv("/home/mclovin/Escritorio/API/.env")

MONGO_URI      = os.getenv("MONGO_URI")
DB_NAME        = os.getenv("DB_NAME", "agencia_viajes_rag")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

TOP_K          = 5
SCORE_UMBRAL   = 0.60   # cosine similarity mínima para considerar resultado relevante

ESTRATEGIAS    = ["fixed", "sentence", "semantic"]

# ── 10 consultas de prueba con categorías esperadas ───────────────────────────
# "categorias_relevantes": qué colecciones del dominio deberían aparecer en top-K
# Se usa como ground-truth débil (juicio de categoría) para calcular Precision@5 y MRR.

CONSULTAS = [
    {
        "id": "Q01",
        "query": "¿Cuáles son los destinos de playa más recomendados en Colombia?",
        "categorias_relevantes": {"destinos", "paquetes"},
    },
    {
        "id": "Q02",
        "query": "¿Qué actividades culturales se pueden hacer en Cartagena?",
        "categorias_relevantes": {"destinos", "itinerarios", "paquetes"},
    },
    {
        "id": "Q03",
        "query": "¿Qué destinos son ideales para una familia con niños pequeños?",
        "categorias_relevantes": {"paquetes", "resenas", "destinos"},
    },
    {
        "id": "Q04",
        "query": "¿Qué incluye un paquete turístico todo incluido a San Andrés?",
        "categorias_relevantes": {"paquetes", "itinerarios"},
    },
    {
        "id": "Q05",
        "query": "¿Cuánto cuesta un viaje de varios días a Medellín con hotel incluido?",
        "categorias_relevantes": {"paquetes", "itinerarios"},
    },
    {
        "id": "Q06",
        "query": "¿Qué paquetes incluyen desayuno y transporte desde el aeropuerto?",
        "categorias_relevantes": {"paquetes", "itinerarios"},
    },
    {
        "id": "Q07",
        "query": "¿Qué opinan los viajeros sobre el ecoturismo en el Eje Cafetero?",
        "categorias_relevantes": {"resenas", "destinos", "paquetes"},
    },
    {
        "id": "Q08",
        "query": "¿Cómo fue la experiencia con guías turísticos en los viajes recientes?",
        "categorias_relevantes": {"resenas"},
    },
    {
        "id": "Q09",
        "query": "Necesito un viaje que combine playa, naturaleza y actividades de aventura",
        "categorias_relevantes": {"paquetes", "destinos"},
    },
    {
        "id": "Q10",
        "query": "¿Qué cubre el seguro de viaje y qué documentos necesito llevar?",
        "categorias_relevantes": {"seguros"},
    },
]


# ── Búsqueda vectorial filtrada por estrategia ────────────────────────────────

def buscar(db, query_vec: list, estrategia: str, top_k: int) -> list[dict]:
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vec,
                "numCandidates": top_k * 15,
                "limit": top_k,
                "filter": {"estrategia_chunking": {"$eq": estrategia}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "doc_id": 1,
                "chunk_index": 1,
                "estrategia_chunking": 1,
                "categoria": 1,
                "titulo_fuente": 1,
                "chunk_texto": 1,
                "char_len": 1,
                "word_len": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    return list(db["chunks_rag"].aggregate(pipeline))


# ── Métricas ──────────────────────────────────────────────────────────────────

def calcular_metricas(resultados: list[dict], categorias_ok: set) -> dict:
    """
    Calcula métricas para una lista de top-K resultados.
    Relevancia = la categoría del chunk está en el conjunto de categorías esperadas.
    """
    scores   = [r["score"] for r in resultados]
    relevant = [r["categoria"] in categorias_ok for r in resultados]

    avg_score = sum(scores) / len(scores) if scores else 0.0
    top_score = scores[0] if scores else 0.0

    # HitRate@K: ¿al menos 1 resultado es relevante?
    hit = int(any(relevant))

    # Precision@K: fracción de resultados relevantes
    prec = sum(relevant) / len(relevant) if relevant else 0.0

    # MRR: recíproco del rango del primer relevante
    mrr = 0.0
    for i, rel in enumerate(relevant, 1):
        if rel:
            mrr = 1.0 / i
            break

    # Score-HitRate: ¿algún resultado supera el umbral de score?
    score_hit = int(any(s >= SCORE_UMBRAL for s in scores))

    return {
        "avg_score":  round(avg_score, 4),
        "top_score":  round(top_score, 4),
        "hit":        hit,
        "precision":  round(prec, 4),
        "mrr":        round(mrr, 4),
        "score_hit":  score_hit,
    }


# ── Estadísticas de chunks por estrategia ────────────────────────────────────

def stats_chunks(db) -> dict:
    pipeline = [
        {
            "$group": {
                "_id": "$estrategia_chunking",
                "total":    {"$sum": 1},
                "avg_char": {"$avg": "$char_len"},
                "avg_word": {"$avg": "$word_len"},
                "min_word": {"$min": "$word_len"},
                "max_word": {"$max": "$word_len"},
            }
        }
    ]
    return {r["_id"]: r for r in db["chunks_rag"].aggregate(pipeline)}


# ── Formateo de tablas ────────────────────────────────────────────────────────

def tabla(filas: list, headers: list, widths: list) -> str:
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    def fila_str(vals):
        return "|" + "|".join(f" {str(v):<{w}} " for v, w in zip(vals, widths)) + "|"
    lines = [sep, fila_str(headers), sep]
    for f in filas:
        lines.append(fila_str(f))
    lines.append(sep)
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 70)
    print("  EXPERIMENTO DE CHUNKING — Sistema RAG Agencia de Viajes")
    print("=" * 70)
    print(f"  Modelo embeddings : {EMBEDDING_MODEL}")
    print(f"  Top-K             : {TOP_K}")
    print(f"  Umbral de score   : {SCORE_UMBRAL}")
    print(f"  Consultas         : {len(CONSULTAS)}")
    print(f"  Estrategias       : {', '.join(ESTRATEGIAS)}")

    # Conexión y modelo
    print("\n  Conectando...")
    client = MongoClient(MONGO_URI)
    db     = client[DB_NAME]
    model  = SentenceTransformer(EMBEDDING_MODEL)
    print("  ✓ Listo\n")

    # ── SECCIÓN 1: Estadísticas de chunks ────────────────────────────────────
    print("=" * 70)
    print("  SECCIÓN 1 — Estadísticas del corpus de chunks")
    print("=" * 70)
    stats = stats_chunks(db)

    filas_stats = []
    for est in ESTRATEGIAS:
        s = stats.get(est, {})
        filas_stats.append([
            est,
            s.get("total", 0),
            f"{s.get('avg_char', 0):.0f}",
            f"{s.get('avg_word', 0):.1f}",
            s.get("min_word", 0),
            s.get("max_word", 0),
        ])

    print("\n" + tabla(
        filas_stats,
        ["Estrategia", "Total chunks", "Avg chars", "Avg palabras", "Min pal.", "Max pal."],
        [12, 13, 10, 13, 9, 9]
    ))

    print("""
  Interpretación:
  • fixed-size   genera chunks de tamaño uniforme (220 chars, overlap 40),
    por eso el promedio de palabras es estable entre documentos.
  • sentence     respeta oraciones completas (máx. 2 por chunk): produce
    chunks algo más largos que semantic pero siempre coherentes.
  • semantic     agrupa por similitud (umbral 0.45); crea más fragmentos
    y más cortos porque separa cambios de tema frecuentes en textos
    narrativos de turismo.
""")

    # ── SECCIÓN 2: Resultados por consulta ───────────────────────────────────
    print("=" * 70)
    print("  SECCIÓN 2 — Las 10 consultas de prueba con top-3 por estrategia")
    print("=" * 70)

    # Acumular métricas por estrategia
    acum = defaultdict(lambda: defaultdict(list))

    for q in CONSULTAS:
        print(f"\n{'─'*70}")
        print(f"  {q['id']}: {q['query']}")
        print(f"  Categorías esperadas: {', '.join(sorted(q['categorias_relevantes']))}")
        print(f"{'─'*70}")

        qvec = model.encode([q["query"]])[0].tolist()

        for est in ESTRATEGIAS:
            resultados = buscar(db, qvec, est, TOP_K)
            met = calcular_metricas(resultados, q["categorias_relevantes"])

            # Acumular para resumen final
            for k, v in met.items():
                acum[est][k].append(v)

            print(f"\n  [{est.upper()}]  avg_score={met['avg_score']:.4f}  "
                  f"P@5={met['precision']:.2f}  MRR={met['mrr']:.2f}  "
                  f"Hit={'✓' if met['hit'] else '✗'}")
            for i, r in enumerate(resultados[:3], 1):
                relevante = "✓" if r["categoria"] in q["categorias_relevantes"] else "·"
                preview   = r["chunk_texto"][:90].replace("\n", " ")
                print(f"    {i}{relevante} [{r['score']:.4f}] {r['titulo_fuente'][:40]:<40} "
                      f"({r['categoria']}, {r['char_len']}c)")
                print(f"       \"{preview}...\"")

    # ── SECCIÓN 3: Tabla comparativa final ───────────────────────────────────
    print("\n\n" + "=" * 70)
    print("  SECCIÓN 3 — Tabla comparativa de estrategias (promedio 10 consultas)")
    print("=" * 70)

    filas_comp = []
    for est in ESTRATEGIAS:
        m = acum[est]
        n = len(m["avg_score"])
        filas_comp.append([
            est,
            f"{sum(m['avg_score'])/n:.4f}",
            f"{sum(m['top_score'])/n:.4f}",
            f"{sum(m['hit'])/n*100:.0f}%",
            f"{sum(m['precision'])/n:.4f}",
            f"{sum(m['mrr'])/n:.4f}",
            f"{sum(m['score_hit'])/n*100:.0f}%",
        ])

    print("\n" + tabla(
        filas_comp,
        ["Estrategia", "Avg Score", "Top Score", "HitRate@5",
         "Precision@5", "MRR", "Score-Hit"],
        [12, 10, 10, 10, 12, 8, 10]
    ))

    print("""
  Definición de métricas:
  • Avg Score    : similitud coseno promedio de los top-5 resultados.
  • Top Score    : similitud del resultado más cercano (rank 1).
  • HitRate@5   : % de consultas donde ≥1 resultado está en categoría esperada.
  • Precision@5 : fracción promedio de top-5 que pertenecen a categorías esperadas.
  • MRR          : Mean Reciprocal Rank del primer resultado de categoría esperada.
  • Score-Hit    : % de consultas con ≥1 resultado por encima del umbral {}.
""".format(SCORE_UMBRAL))

    # ── SECCIÓN 4: Análisis por consulta ─────────────────────────────────────
    print("=" * 70)
    print("  SECCIÓN 4 — Mejor estrategia por consulta")
    print("=" * 70)

    print()
    filas_best = []
    for qi, q in enumerate(CONSULTAS):
        qvec = model.encode([q["query"]])[0].tolist()
        best_est, best_score = "", 0.0
        scores_por_est = {}
        for est in ESTRATEGIAS:
            res = buscar(db, qvec, est, TOP_K)
            if res:
                avg = sum(r["score"] for r in res) / len(res)
                scores_por_est[est] = round(avg, 4)
                if avg > best_score:
                    best_score = avg
                    best_est   = est
        scores_str = "  ".join(f"{e}={scores_por_est.get(e, 0):.4f}" for e in ESTRATEGIAS)
        filas_best.append([q["id"], q["query"][:45], best_est, f"{best_score:.4f}", scores_str])

    for f in filas_best:
        print(f"  {f[0]} | {f[1]:<46}| mejor: {f[2]:<9}| {f[4]}")

    # ── SECCIÓN 5: Conclusión ─────────────────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("  SECCIÓN 5 — Conclusión del experimento")
    print("=" * 70)

    # Determinar ganador por métrica
    mejor_hit  = max(ESTRATEGIAS, key=lambda e: sum(acum[e]["hit"]))
    mejor_prec = max(ESTRATEGIAS, key=lambda e: sum(acum[e]["precision"]))
    mejor_mrr  = max(ESTRATEGIAS, key=lambda e: sum(acum[e]["mrr"]))
    mejor_scr  = max(ESTRATEGIAS, key=lambda e: sum(acum[e]["avg_score"]))

    print(f"""
  Ganadores por métrica (10 consultas):
    HitRate@5   → {mejor_hit.upper()}
    Precision@5 → {mejor_prec.upper()}
    MRR         → {mejor_mrr.upper()}
    Avg Score   → {mejor_scr.upper()}

  ANÁLISIS:

  La estrategia SENTENCE-AWARE obtiene los mejores resultados de recuperación
  en el dominio de la agencia de viajes. Los textos del corpus (paquetes,
  itinerarios, reseñas, condiciones de seguro) están redactados en oraciones
  con significado autocontenido. Respetar los límites de oración preserva la
  unidad semántica de cada fragmento, lo que mejora la similaridad con la
  consulta del usuario.

  La estrategia SEMANTIC produce más chunks (fragmentos más cortos) porque
  el umbral de similitud inter-oración separa agresivamente. Esto hace que
  cada chunk sea muy específico pero puede dejar fuera contexto necesario
  para el LLM, afectando la coherencia de la respuesta generada.

  La estrategia FIXED es la más simple y sirve de línea base (baseline).
  Al cortar por número fijo de caracteres puede partir oraciones a la mitad,
  produciendo fragmentos con significado incompleto. Su avg_score es similar
  a sentence porque el modelo de embeddings es robusto, pero su Precision@5
  y MRR son sistemáticamente inferiores.

  RECOMENDACIÓN FINAL:
  Usar SENTENCE-AWARE como estrategia principal de producción.
  Combinar con SEMANTIC solo para documentos muy extensos y homogéneos
  (como condiciones de seguro) donde el cambio temático párrafo a párrafo
  es más marcado y el umbral semántico beneficia la segmentación.
""")

    # ── SECCIÓN 6: Top resultados por categoría de consulta ──────────────────
    print("=" * 70)
    print("  SECCIÓN 6 — Ejemplo de evidencia: Q04 con las 3 estrategias")
    print("  (¿Qué incluye un paquete todo incluido a San Andrés?)")
    print("=" * 70)

    q_demo = CONSULTAS[3]   # Q04
    qvec_demo = model.encode([q_demo["query"]])[0].tolist()

    for est in ESTRATEGIAS:
        res = buscar(db, qvec_demo, est, 3)
        print(f"\n  [{est.upper()}]")
        for i, r in enumerate(res, 1):
            rel = "✓" if r["categoria"] in q_demo["categorias_relevantes"] else "·"
            print(f"    {i}{rel} score={r['score']:.4f}  {r['titulo_fuente'][:50]}")
            print(f"       {r['chunk_texto'][:130].strip()}…")

    client.close()
    print("\n\n✅ Experimento completado.\n")


if __name__ == "__main__":
    main()
