import { assetUrl, getApiBase, setApiBase } from "./api.js";

const links = [
  ["index.html", "Inicio"],
  ["destinos.html", "Destinos"],
  ["paquetes.html", "Paquetes"],
  ["search.html", "Texto a texto"],
  ["multimedia.html", "Texto a imagen"],
  ["clip.html", "Imagen a imagen"],
  ["multimodal.html", "Multimodal"],
  ["rag.html", "RAG"],
  ["chunking.html", "Chunking"],
];

export function initShell(title, subtitle) {
  const page = document.body.dataset.page || "";
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div class="app-shell">
      <aside class="sidebar">
        <a class="brand" href="${page === "home" ? "index.html" : "../index.html"}">
          <span class="brand-mark">BD</span>
          <span>
            <span class="brand-title">Turismo NoSQL</span>
            <span class="brand-subtitle">MongoDB Atlas + RAG</span>
          </span>
        </a>
        <nav class="nav">
          ${links
            .map(([href, label]) => {
              const finalHref = page === "home"
                ? href === "index.html" ? "index.html" : `pages/${href}`
                : href === "index.html" ? "../index.html" : href;
              const active = document.location.pathname.endsWith(href);
              return `<a class="${active ? "active" : ""}" href="${finalHref}">${label}</a>`;
            })
            .join("")}
        </nav>
      </aside>
      <main class="main">
        <header class="topbar">
          <div>
            <h1>${title}</h1>
            <p>${subtitle}</p>
          </div>
          <form class="api-config" id="api-config">
            <input id="api-base" aria-label="URL backend" value="${getApiBase()}">
            <button class="btn ghost" type="submit">Guardar API</button>
          </form>
        </header>
        <div class="content" id="page-content"></div>
      </main>
    </div>`
  );

  document.querySelector("#api-config").addEventListener("submit", (event) => {
    event.preventDefault();
    setApiBase(document.querySelector("#api-base").value);
    toast("URL del backend actualizada.");
  });
}

export function content() {
  return document.querySelector("#page-content");
}

export function showLoader(target, message = "Consultando backend...") {
  target.innerHTML = `<span class="loader">${message}</span>`;
}

export function showError(target, error) {
  target.innerHTML = `<div class="error">${escapeHtml(error.message || error)}</div>`;
}

export function toast(message) {
  const box = document.createElement("div");
  box.className = "card";
  box.style.position = "fixed";
  box.style.right = "18px";
  box.style.bottom = "18px";
  box.style.zIndex = "5";
  box.textContent = message;
  document.body.appendChild(box);
  setTimeout(() => box.remove(), 2200);
}

export function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function formatScore(score) {
  return typeof score === "number" ? score.toFixed(4) : "sin score";
}

export function statCard(label, value) {
  return `<article class="stat-card"><div class="stat-value">${value ?? 0}</div><div class="stat-label">${label}</div></article>`;
}

export function imageCard(item) {
  return `<article class="card image-card">
    <img src="${assetUrl(item.url)}" alt="${escapeHtml(item.titulo || item.nombre_destino || "Imagen turística")}" loading="lazy">
    <div class="body">
      <h3>${escapeHtml(item.titulo || item.nombre_destino || "Resultado visual")}</h3>
      <p>${escapeHtml(item.descripcion || item.descripcion_visual || "")}</p>
      <div class="meta-row">
        ${item.score != null ? `<span class="score">score ${formatScore(item.score)}</span>` : ""}
        ${item.tipo ? `<span class="pill">${escapeHtml(item.tipo)}</span>` : ""}
      </div>
    </div>
  </article>`;
}

export function destinationCard(destino, images = []) {
  const firstImage = images[0];
  return `<article class="card">
    ${firstImage ? `<img class="preview-image" src="${assetUrl(firstImage.url)}" alt="${escapeHtml(destino.nombre)}">` : ""}
    <h3>${escapeHtml(destino.nombre)}</h3>
    <p>${escapeHtml(destino.descripcion || "").slice(0, 420)}${(destino.descripcion || "").length > 420 ? "..." : ""}</p>
    <div class="meta-row">
      <span class="pill">${escapeHtml(destino.categoria || "destino")}</span>
      <span class="muted">${images.length} imágenes</span>
    </div>
  </article>`;
}

export function packageCard(paquete) {
  return `<article class="card">
    <h3>${escapeHtml(paquete.titulo || paquete.nombre || "Paquete turístico")}</h3>
    <p>${escapeHtml(paquete.descripcion || "").slice(0, 360)}${(paquete.descripcion || "").length > 360 ? "..." : ""}</p>
    <div class="meta-row">
      <span class="pill">${escapeHtml(paquete.tipo || "Plan")}</span>
      <span class="score">$${Number(paquete.precio || paquete.precio_base || 0).toLocaleString("es-CO")}</span>
      <span class="muted">${paquete.duracion_dias || "-"} días</span>
    </div>
  </article>`;
}

export function resultCard(result) {
  return `<article class="card">
    <h3>Documento ${escapeHtml(result.doc_id || result.id || "")}</h3>
    <p>${escapeHtml(result.texto || "")}</p>
    <div class="meta-row">
      <span class="score">score ${formatScore(result.score)}</span>
      <span class="pill">${escapeHtml(result.metadata?.estrategia_chunking || "chunk")}</span>
      <span class="muted">chunk ${result.metadata?.chunk_index ?? "-"}</span>
    </div>
  </article>`;
}

export function exampleButtons(container, input, examples) {
  container.innerHTML = examples
    .map((item) => `<button class="example" type="button">${escapeHtml(item)}</button>`)
    .join("");
  container.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.textContent;
      input.focus();
    });
  });
}
