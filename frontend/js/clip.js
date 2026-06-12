import { Api } from "./api.js";
import { content, exampleButtons, imageCard, initShell, showError, showLoader } from "./ui.js";

export function initClip() {
  initShell("Imagen a imagen CLIP", "Carga una imagen local y encuentra imágenes similares en multimedia_clip.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <form id="clip-form" class="grid two">
      <div class="field"><label for="file">Imagen local</label><input id="file" type="file" accept="image/*" required></div>
      <div class="field"><label for="limit">Límite</label><input id="limit" type="number" min="1" max="30" value="8"></div>
      <button class="btn" type="submit">Buscar similares</button>
    </form>
  </section>
  <section class="grid two">
    <div class="card"><h3>Imagen original</h3><div id="preview" class="muted">Selecciona un archivo para ver la previsualización.</div></div>
    <div id="clip-status"></div>
  </section>
  <div id="clip-results"></div>`;
  const fileInput = document.querySelector("#file");
  fileInput.addEventListener("change", () => renderPreview(fileInput.files[0]));
  document.querySelector("#clip-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = document.querySelector("#clip-results");
    const status = document.querySelector("#clip-status");
    showLoader(status, "Calculando embedding CLIP...");
    target.innerHTML = "";
    try {
      const response = await Api.clipImageSearch(fileInput.files[0], Number(document.querySelector("#limit").value));
      status.innerHTML = `<article class="card"><h3>Resultado</h3><p>${response.total} imágenes similares encontradas.</p></article>`;
      target.innerHTML = `<div class="grid cards">${response.results.map(imageCard).join("")}</div>`;
    } catch (error) {
      showError(status, error);
    }
  });
}

export function initClipText() {
  initShell("Texto a imagen CLIP", "Consulta textual sobre embeddings CLIP de imágenes.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <form id="clip-text-form" class="grid two">
      <div class="field"><label for="query">Consulta</label><input id="query" required minlength="2" value="cultura cafetera"></div>
      <div class="field"><label for="limit">Límite</label><input id="limit" type="number" min="1" max="30" value="8"></div>
      <button class="btn" type="submit">Buscar con CLIP</button>
    </form>
    <div class="examples" id="examples"></div>
  </section>
  <div id="clip-text-results"></div>`;
  exampleButtons(document.querySelector("#examples"), document.querySelector("#query"), [
    "playas cristalinas",
    "montañas verdes",
    "arquitectura colonial",
  ]);
  document.querySelector("#clip-text-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = document.querySelector("#clip-text-results");
    showLoader(target, "Buscando en multimedia_clip...");
    try {
      const response = await Api.clipTextSearch({
        query: document.querySelector("#query").value,
        limit: Number(document.querySelector("#limit").value),
      });
      target.innerHTML = `<p class="muted">${response.total} resultados para "${response.query}"</p><div class="grid cards">${response.results
        .map(imageCard)
        .join("")}</div>`;
    } catch (error) {
      showError(target, error);
    }
  });
}

function renderPreview(file) {
  const preview = document.querySelector("#preview");
  if (!file) {
    preview.textContent = "Selecciona un archivo para ver la previsualización.";
    return;
  }
  const url = URL.createObjectURL(file);
  preview.innerHTML = `<img class="preview-image" src="${url}" alt="Imagen seleccionada">`;
}
