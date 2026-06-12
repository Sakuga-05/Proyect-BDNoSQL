import { Api } from "./api.js";
import { content, exampleButtons, imageCard, initShell, showError, showLoader } from "./ui.js";

export function initMultimedia() {
  initShell("Texto a imagen", "Búsqueda semántica en la colección multimedia con embeddings de texto.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <form id="multimedia-form" class="grid two">
      <div class="field"><label for="query">Consulta textual</label><input id="query" required minlength="2" value="playas cristalinas"></div>
      <div class="field"><label for="limit">Límite</label><input id="limit" type="number" min="1" max="30" value="8"></div>
      <div class="field"><label for="tipo">Tipo</label><input id="tipo" placeholder="imagen"></div>
      <button class="btn" type="submit">Buscar imágenes</button>
    </form>
    <div class="examples" id="examples"></div>
  </section>
  <div id="multimedia-results"></div>`;
  exampleButtons(document.querySelector("#examples"), document.querySelector("#query"), [
    "playas cristalinas",
    "montañas",
    "cultura cafetera",
  ]);
  document.querySelector("#multimedia-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = document.querySelector("#multimedia-results");
    showLoader(target, "Buscando imágenes por texto...");
    try {
      const tipo = document.querySelector("#tipo").value.trim() || null;
      const response = await Api.multimediaSearch({
        query: document.querySelector("#query").value,
        limit: Number(document.querySelector("#limit").value),
        tipo,
      });
      target.innerHTML = `<p class="muted">${response.total} resultados para "${response.query}"</p><div class="grid cards">${response.results
        .map(imageCard)
        .join("")}</div>`;
    } catch (error) {
      showError(target, error);
    }
  });
}
