import { Api } from "./api.js";
import { content, imageCard, initShell, showError, showLoader } from "./ui.js";

export function initMultimodal() {
  initShell("Búsqueda multimodal", "Combina texto e imagen opcional usando embeddings CLIP.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <form id="multimodal-form" class="grid two">
      <div class="field"><label for="query">Consulta textual</label><input id="query" value="playas con cultura local"></div>
      <div class="field"><label for="file">Imagen opcional</label><input id="file" type="file" accept="image/*"></div>
      <div class="field"><label for="limit">Límite</label><input id="limit" type="number" min="1" max="30" value="8"></div>
      <button class="btn" type="submit">Buscar</button>
    </form>
  </section>
  <section class="grid two">
    <div class="card"><h3>Consulta</h3><p id="query-summary" class="muted">Texto y/o imagen seleccionada.</p><div id="preview"></div></div>
    <div id="multimodal-status"></div>
  </section>
  <div id="multimodal-results"></div>`;
  const fileInput = document.querySelector("#file");
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    document.querySelector("#preview").innerHTML = file
      ? `<img class="preview-image" src="${URL.createObjectURL(file)}" alt="Imagen de consulta">`
      : "";
  });
  document.querySelector("#multimodal-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = document.querySelector("#multimodal-results");
    const status = document.querySelector("#multimodal-status");
    const query = document.querySelector("#query").value.trim();
    const file = fileInput.files[0] || null;
    document.querySelector("#query-summary").textContent = query || "Solo imagen";
    showLoader(status, "Ejecutando búsqueda multimodal...");
    target.innerHTML = "";
    try {
      const response = await Api.multimodalSearch({
        query,
        file,
        limit: Number(document.querySelector("#limit").value),
      });
      status.innerHTML = `<article class="card"><h3>Resultado</h3><p>${response.total} coincidencias visuales.</p></article>`;
      target.innerHTML = `<div class="grid cards">${response.results.map(imageCard).join("")}</div>`;
    } catch (error) {
      showError(status, error);
    }
  });
}
