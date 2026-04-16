<!--
Archivo: plan_experimento.md
Descripción: Documento que detalla el plan experimental para el proyecto de chunking.
Incluye estrategias implementadas, consultas de prueba y criterios de evaluación.
-->

# Plan de Experimento de Chunking

## Estrategias Implementadas

| Estrategia | Parámetros | Uso recomendado |
|------------|------------|-----------------|
| Fixed-size | chunk_size=500, overlap=50 | Textos homogéneos |
| Sentence-aware | max_oraciones=3, overlap=1 | Textos narrativos |
| Semantic | umbral=0.75 | Documentos técnicos |

## Consultas de Prueba (10)

1. ¿Cuáles son los destinos de playa más recomendados en Colombia?
2. ¿Qué actividades culturales se pueden hacer en Cartagena?
3. Menciona tres destinos ideales para una familia con niños
4. ¿Qué incluye un paquete turístico a San Andrés?
5. ¿Cuál es el precio promedio de un viaje de 5 días a Medellín?
6. ¿Qué alojamientos ofrecen desayuno incluido?
7. ¿Qué opinan los viajeros sobre el ecoturismo en el Eje Cafetero?
8. ¿Cuál es la mejor reseña escrita sobre un guía turístico?
9. Necesito un viaje que combine playa y naturaleza
10. ¿Qué requisitos necesito para viajar con menores de edad?

## Criterios de Evaluación

- ✓ Mínimo 2 estrategias implementadas
- ✓ Campo `estrategia_chunking` en MongoDB
- ✓ Análisis comparativo en informe