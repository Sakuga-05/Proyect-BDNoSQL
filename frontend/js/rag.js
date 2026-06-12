import { Api } from "./api.js";
import { content, escapeHtml, exampleButtons, formatScore, initShell, showError, showLoader } from "./ui.js";

export function initRag() {
  initShell("RAG turístico", "Pregunta al sistema y revisa respuesta, contexto recuperado y fuentes.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <form id="rag-form" class="grid two">
      <div class="field"><label for="question">Pregunta</label><textarea id="question" required minlength="3">¿Cuál es el mejor destino para luna de miel?</textarea></div>
      <div class="grid">
        <div class="field"><label for="strategy">Estrategia</label><select id="strategy"><option>sentence-aware</option><option>fixed-size</option></select></div>
        <div class="field"><label for="limit">Fuentes</label><input id="limit" type="number" min="1" max="10" value="5"></div>
        <button class="btn" type="submit">Preguntar</button>
      </div>
    </form>
    <div class="examples" id="examples"></div>
  </section>
  <div id="rag-results"></div>`;
  exampleButtons(document.querySelector("#examples"), document.querySelector("#question"), [
    "¿Cuál es el mejor destino para luna de miel?",
    "¿Qué destinos tienen actividades extremas?",
    "¿Dónde puedo practicar buceo?",
  ]);
  document.querySelector("#rag-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = document.querySelector("#rag-results");
    showLoader(target, "Recuperando contexto y generando respuesta...");
    try {
      const response = await Api.rag({
        question: document.querySelector("#question").value,
        limit: Number(document.querySelector("#limit").value),
        estrategia_chunking: document.querySelector("#strategy").value,
      });
      target.innerHTML = `<section class="card">
        <h3>Respuesta generada</h3>
        <p>${escapeHtml(response.answer)}</p>
        <div class="meta-row"><span class="pill">query ${escapeHtml(response.query_id || "sin persistir")}</span></div>
      </section>
      <section class="section">
        <h2 class="section-title">Fuentes utilizadas</h2>
        <div class="result-layout">${response.sources
          .map(
            (source) => `<article class="card source-card">
              <h3>Documento ${escapeHtml(source.doc_id || "")}</h3>
              <p>${escapeHtml(source.texto)}</p>
              <div class="meta-row">
                <span class="score">score ${formatScore(source.score)}</span>
                <span class="pill">chunk ${source.chunk_index ?? "-"}</span>
              </div>
            </article>`
          )
          .join("")}</div>
      </section>`;
    } catch (error) {
      showError(target, error);
    }
  });
}
