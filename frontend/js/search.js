import { Api } from "./api.js";
import {
  content,
  destinationCard,
  exampleButtons,
  initShell,
  packageCard,
  resultCard,
  showError,
  showLoader,
  statCard,
} from "./ui.js";

export async function initHome() {
  initShell("Panel de demostración", "Resumen del backend turístico y accesos de sustentación.");
  const root = content();
  root.innerHTML = `<section class="hero-band">
    <div class="intro-panel">
      <h2>Explorador turístico con MongoDB Atlas</h2>
      <p>Frontend vanilla para demostrar catálogos, Vector Search, RAG, embeddings multimedia, CLIP y comparación de chunking con datos reales del backend.</p>
    </div>
    <div class="quick-panel">
      <h3 class="section-title">Estado del backend</h3>
      <div id="health" class="muted">Verificando conexión...</div>
    </div>
  </section>
  <section class="section">
    <h2 class="section-title">Métricas principales</h2>
    <div id="stats" class="grid stats"></div>
  </section>`;

  try {
    const [health, stats] = await Promise.all([Api.health(), Api.stats()]);
    document.querySelector("#health").textContent = `${health.status} · ${health.app}`;
    document.querySelector("#stats").innerHTML = [
      statCard("Destinos", stats.destino),
      statCard("Paquetes", stats.paqueteTuristico),
      statCard("Imágenes multimedia", stats.multimedia),
      statCard("Reseñas", stats.resena),
      statCard("Chunks RAG", stats.chunks),
      statCard("Participantes", stats.participante),
    ].join("");
  } catch (error) {
    showError(document.querySelector("#stats"), error);
    document.querySelector("#health").textContent = "No se pudo conectar con el backend.";
  }
}

export async function initDestinos() {
  initShell("Destinos", "Consulta de destinos e imágenes asociadas almacenadas en MongoDB.");
  const root = content();
  root.innerHTML = `<div id="destinos-results"></div>`;
  const target = document.querySelector("#destinos-results");
  showLoader(target);
  try {
    const [destinos, multimedia] = await Promise.all([
      Api.list("destino", 100),
      Api.list("multimedia", 200),
    ]);
    const imagesByDestino = new Map();
    multimedia.results.forEach((item) => {
      const key = item.destino_id || item.metadata?.destino_id;
      if (!imagesByDestino.has(key)) imagesByDestino.set(key, []);
      imagesByDestino.get(key).push(item);
    });
    target.innerHTML = `<div class="grid cards">${destinos.results
      .map((destino) => destinationCard(destino, imagesByDestino.get(destino._id) || []))
      .join("")}</div>`;
  } catch (error) {
    showError(target, error);
  }
}

export async function initPaquetes() {
  initShell("Paquetes turísticos", "Listado de paquetes con filtros locales por tipo y precio.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <div class="toolbar">
      <div class="field"><label for="tipo">Tipo</label><select id="tipo"><option value="">Todos</option></select></div>
      <div class="field"><label for="precio">Precio máximo</label><input id="precio" type="number" min="0" step="50000" placeholder="Ej: 1500000"></div>
      <button class="btn" id="filtrar">Filtrar</button>
    </div>
  </section>
  <div id="paquetes-results"></div>`;
  const target = document.querySelector("#paquetes-results");
  showLoader(target);
  try {
    const data = await Api.list("paqueteTuristico", 150);
    const tipos = [...new Set(data.results.map((p) => p.tipo).filter(Boolean))].sort();
    document.querySelector("#tipo").insertAdjacentHTML(
      "beforeend",
      tipos.map((tipo) => `<option>${tipo}</option>`).join("")
    );
    const render = () => {
      const tipo = document.querySelector("#tipo").value;
      const max = Number(document.querySelector("#precio").value || Infinity);
      const filtered = data.results.filter((paquete) => {
        const price = Number(paquete.precio || paquete.precio_base || 0);
        return (!tipo || paquete.tipo === tipo) && price <= max;
      });
      target.innerHTML = `<p class="muted">${filtered.length} paquetes encontrados</p><div class="grid cards">${filtered
        .map(packageCard)
        .join("")}</div>`;
    };
    document.querySelector("#filtrar").addEventListener("click", render);
    render();
  } catch (error) {
    showError(target, error);
  }
}

export function initTextSearch() {
  initShell("Búsqueda texto a texto", "Vector Search sobre chunks generados para RAG.");
  const root = content();
  root.innerHTML = `<section class="form-panel">
    <form id="search-form" class="grid two">
      <div class="field"><label for="query">Consulta</label><input id="query" required minlength="2" value="playas del caribe"></div>
      <div class="field"><label for="strategy">Estrategia</label><select id="strategy"><option value="">Todas</option><option>fixed-size</option><option>sentence-aware</option></select></div>
      <div class="field"><label for="limit">Límite</label><input id="limit" type="number" min="1" max="20" value="5"></div>
      <button class="btn" type="submit">Buscar</button>
    </form>
    <div class="examples" id="examples"></div>
  </section>
  <div id="search-results"></div>`;
  exampleButtons(document.querySelector("#examples"), document.querySelector("#query"), [
    "playas del caribe",
    "aventura extrema",
    "destinos para parejas",
  ]);
  document.querySelector("#search-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = document.querySelector("#search-results");
    showLoader(target, "Ejecutando Vector Search...");
    try {
      const strategy = document.querySelector("#strategy").value || null;
      const response = await Api.searchText({
        query: document.querySelector("#query").value,
        limit: Number(document.querySelector("#limit").value),
        estrategia_chunking: strategy,
      });
      target.innerHTML = `<p class="muted">${response.total} resultados para "${response.query}"</p><div class="result-layout">${response.results
        .map(resultCard)
        .join("")}</div>`;
    } catch (error) {
      showError(target, error);
    }
  });
}
