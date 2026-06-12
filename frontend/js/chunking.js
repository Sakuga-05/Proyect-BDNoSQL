import { Api } from "./api.js";
import { content, escapeHtml, initShell, showError, showLoader } from "./ui.js";

const sampleText =
  "Cartagena combina playas del Caribe, arquitectura colonial, gastronomía local y recorridos históricos por murallas, plazas y fortalezas. " +
  "Un itinerario turístico puede incluir navegación hacia islas cercanas, caminatas guiadas por el centro amurallado, experiencias culinarias y espacios de descanso. " +
  "La comparación de chunking permite observar cómo una estrategia fija corta por tamaño, mientras una estrategia consciente de oraciones conserva mejor las ideas completas.";

export function initChunking() {
  initShell("Comparación de chunking", "Evalúa fixed-size frente a sentence-aware y visualiza previews.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <form id="chunking-form" class="grid">
      <div class="field"><label for="doc-id">Doc ID</label><input id="doc-id" value="demo-frontend"></div>
      <div class="field"><label for="text">Texto</label><textarea id="text" required minlength="20">${sampleText}</textarea></div>
      <div class="checks">
        <label class="check"><input type="checkbox" name="strategy" value="fixed-size" checked> fixed-size</label>
        <label class="check"><input type="checkbox" name="strategy" value="sentence-aware" checked> sentence-aware</label>
        <label class="check"><input id="persist" type="checkbox"> persistir chunks</label>
      </div>
      <button class="btn" type="submit">Comparar</button>
    </form>
  </section>
  <div id="chunking-results"></div>`;
  document.querySelector("#chunking-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = document.querySelector("#chunking-results");
    showLoader(target, "Comparando estrategias...");
    try {
      const strategies = [...document.querySelectorAll("input[name='strategy']:checked")].map((item) => item.value);
      const response = await Api.compareChunking({
        doc_id: document.querySelector("#doc-id").value,
        text: document.querySelector("#text").value,
        strategies,
        persist: document.querySelector("#persist").checked,
      });
      target.innerHTML = `<section class="grid stats">${response.stats
        .map(
          (stat) => `<article class="stat-card">
            <div class="stat-value">${stat.total_chunks}</div>
            <div class="stat-label">${escapeHtml(stat.estrategia_chunking)} · promedio ${Math.round(stat.promedio_caracteres)} caracteres</div>
          </article>`
        )
        .join("")}</section>
      <section class="section">
        <h2 class="section-title">Previews</h2>
        <div class="result-layout">${response.previews
          .map(
            (preview) => `<article class="card chunk-preview">
              <h3>${escapeHtml(preview.estrategia_chunking)} · chunk ${preview.chunk_index}</h3>
              <p>${escapeHtml(preview.chunk_texto)}</p>
              <span class="muted">${preview.caracteres} caracteres</span>
            </article>`
          )
          .join("")}</div>
      </section>`;
    } catch (error) {
      showError(target, error);
    }
  });
}
