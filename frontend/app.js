'use strict';

/* ─────────────────────────────────────────
   Config — change this if the API runs
   on a different host/port
───────────────────────────────────────── */
const API_BASE = 'http://localhost:8000';

/* ─────────────────────────────────────────
   Utilities
───────────────────────────────────────── */

function $(id) { return document.getElementById(id); }

/** Safely escape HTML to prevent XSS when inserting user-originated data */
function esc(str) {
  if (str == null) return '';
  const d = document.createElement('div');
  d.textContent = String(str);
  return d.innerHTML;
}

function resolveUrl(url) {
  if (!url) return null;
  if (/^https?:\/\//.test(url)) return url;
  // Encode each segment individually so special chars (á, ñ, spaces, etc.) work in browsers
  const encoded = url.split('/').map(seg => encodeURIComponent(seg)).join('/');
  return API_BASE + encoded;
}

function scoreLabel(score) {
  if (score == null) return null;
  return (score * 100).toFixed(1) + '%';
}

function badge(text, cls = 'slate') {
  return `<span class="badge badge-${cls}">${esc(text)}</span>`;
}

function setHtml(id, html) {
  $(id).innerHTML = html;
}

function showLoading(id, msg = 'Procesando...') {
  setHtml(id, `
    <div class="loading-box">
      <div class="spinner"></div>
      <p>${esc(msg)}</p>
    </div>
  `);
}

function showError(id, msg) {
  setHtml(id, `
    <div class="error-box">
      <span class="error-icon">⚠️</span>
      <span>${esc(msg)}</span>
    </div>
  `);
}

async function apiPost(path, body) {
  const res = await fetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    let detail;
    try { detail = JSON.parse(text)?.detail; } catch { /* empty */ }
    throw new Error(detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function apiFormPost(path, formData) {
  const res = await fetch(API_BASE + path, { method: 'POST', body: formData });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    let detail;
    try { detail = JSON.parse(text)?.detail; } catch { /* empty */ }
    throw new Error(detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

/* ─────────────────────────────────────────
   Health Check
───────────────────────────────────────── */

async function checkHealth() {
  try {
    const data = await fetch(API_BASE + '/health').then(r => r.json());
    $('statusDot').className = 'status-dot ok';
    $('statusLabel').textContent = data.status === 'ok' ? 'API activa' : data.status;
  } catch {
    $('statusDot').className = 'status-dot error';
    $('statusLabel').textContent = 'API no disponible';
  }
}

/* ─────────────────────────────────────────
   Tab Navigation
───────────────────────────────────────── */

function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      $('tab-' + tab).classList.add('active');
    });
  });
}

/* ─────────────────────────────────────────
   File Dropzones
───────────────────────────────────────── */

function initDropzone(inputId, zoneId, bodyId) {
  const input = $(inputId);
  const zone  = $(zoneId);
  const body  = $(bodyId);
  if (!input || !zone || !body) return;

  function showPreview(file) {
    if (!file?.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = e => {
      body.innerHTML = `
        <div class="dz-preview-img" style="background-image:url('${e.target.result}')"></div>
        <p class="dropzone-filename">📎 ${esc(file.name)}</p>
      `;
      zone.classList.add('has-preview');
    };
    reader.readAsDataURL(file);
  }

  input.addEventListener('change', () => { if (input.files[0]) showPreview(input.files[0]); });

  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      showPreview(file);
    }
  });
}

/* ─────────────────────────────────────────
   Shared: Media Grid renderer
   Used by multimedia, CLIP text/image, multimodal
───────────────────────────────────────── */

function renderMediaGrid(results, containerId) {
  if (!results?.length) {
    return setHtml(containerId, `
      <div class="empty-box">
        <div class="empty-icon">🔍</div>
        <p>No se encontraron resultados para esta búsqueda.</p>
      </div>
    `);
  }

  const cards = results.map(r => {
    const url   = resolveUrl(r.url);
    const title = r.titulo || r.nombre_destino || '—';
    const desc  = r.descripcion || r.descripcion_visual || '';

    const imgHtml = url
      ? `<img class="media-card-img" src="${esc(url)}" alt="${esc(title)}" loading="lazy">`
      : `<div class="media-card-placeholder">🏞️</div>`;

    const typeBadge  = r.tipo  ? badge(r.tipo, 'blue')   : '';
    const scoreBadge = r.score != null ? badge(scoreLabel(r.score), 'score') : '';
    const destBadge  = (r.metadata?.nombre_destino) ? badge(r.metadata.nombre_destino, 'slate') : '';

    return `
      <div class="media-card">
        ${imgHtml}
        <div class="media-card-body">
          <div class="media-card-title" title="${esc(title)}">${esc(title)}</div>
          ${desc ? `<div class="media-card-desc" title="${esc(desc)}">${esc(desc)}</div>` : ''}
          <div class="media-card-footer">${typeBadge}${destBadge}${scoreBadge}</div>
        </div>
      </div>
    `;
  }).join('');

  setHtml(containerId, `
    <div class="results-meta">📷 ${results.length} resultado${results.length !== 1 ? 's' : ''}</div>
    <div class="media-grid">${cards}</div>
  `);

  /* attach image error handlers after DOM is ready */
  $(containerId).querySelectorAll('.media-card-img').forEach(img => {
    img.onerror = function () {
      const ph = document.createElement('div');
      ph.className = 'media-card-placeholder';
      ph.textContent = '🏞️';
      this.replaceWith(ph);
    };
  });
}

/* ─────────────────────────────────────────
   RAG
───────────────────────────────────────── */

function initRag() {
  $('ragForm').addEventListener('submit', async e => {
    e.preventDefault();
    const question           = $('ragQuestion').value.trim();
    const limit              = parseInt($('ragLimit').value) || 5;
    const estrategia_chunking = $('ragStrategy').value;

    showLoading('ragResults', 'La IA está generando tu respuesta con Gemini...');

    try {
      const data = await apiPost('/rag', { question, limit, estrategia_chunking });
      renderRagResult(data);
    } catch (err) {
      showError('ragResults', err.message);
    }
  });
}

function renderRagResult(data) {
  const sources = (data.sources || []).map(s => {
    const docBadge   = s.doc_id       ? badge(s.doc_id, 'slate')                     : '';
    const idxBadge   = s.chunk_index != null ? badge(`Chunk #${s.chunk_index}`, 'purple') : '';
    const scoreBadge = s.score != null       ? badge(scoreLabel(s.score), 'score')        : '';
    return `
      <div class="source-card">
        <div class="source-card-meta">${docBadge}${idxBadge}${scoreBadge}</div>
        <div class="source-card-text">${esc(s.texto || '')}</div>
      </div>
    `;
  }).join('');

  const sourcesBlock = data.sources?.length
    ? `<div class="sources-header">📄 Fuentes utilizadas (${data.sources.length})</div>${sources}`
    : '';

  const queryIdBlock = data.query_id
    ? `<div class="results-meta">🆔 Query ID: ${esc(data.query_id)}</div>`
    : '';

  setHtml('ragResults', `
    <div class="rag-answer-box">
      <div class="rag-answer-label">✨ Respuesta generada por IA</div>
      <div class="rag-answer-text">${esc(data.answer || '')}</div>
    </div>
    ${queryIdBlock}
    ${sourcesBlock}
  `);
}

/* ─────────────────────────────────────────
   Semantic Search
───────────────────────────────────────── */

function initSearch() {
  $('searchForm').addEventListener('submit', async e => {
    e.preventDefault();
    const query              = $('searchQuery').value.trim();
    const limit              = parseInt($('searchLimit').value) || 5;
    const estrategia         = $('searchStrategy').value || null;
    const filtersRaw         = $('searchFilters').value.trim();

    let filters = null;
    if (filtersRaw) {
      try { filters = JSON.parse(filtersRaw); }
      catch { return showError('searchResults', 'Filtros JSON inválidos — verifica la sintaxis.'); }
    }

    showLoading('searchResults', 'Buscando fragmentos relevantes...');

    try {
      const body = { query, limit };
      if (estrategia) body.estrategia_chunking = estrategia;
      if (filters)    body.filters = filters;
      const data = await apiPost('/search', body);
      renderSearchResults(data);
    } catch (err) {
      showError('searchResults', err.message);
    }
  });
}

function renderSearchResults(data) {
  if (!data.results?.length) {
    return setHtml('searchResults', `
      <div class="empty-box">
        <div class="empty-icon">🔍</div>
        <p>No se encontraron fragmentos para "<strong>${esc(data.query)}</strong>".</p>
      </div>
    `);
  }

  const cards = data.results.map(r => {
    const meta       = r.metadata || {};
    const scoreBadge = r.score != null         ? badge(scoreLabel(r.score), 'score')    : '';
    const docBadge   = r.doc_id                ? badge(r.doc_id, 'slate')               : '';
    const idxBadge   = meta.chunk_index != null ? badge(`Chunk #${meta.chunk_index}`, 'purple') : '';
    const stratBadge = meta.estrategia_chunking  ? badge(meta.estrategia_chunking, 'blue')      : '';
    return `
      <div class="chunk-card">
        <div class="chunk-card-meta">${scoreBadge}${docBadge}${idxBadge}${stratBadge}</div>
        <div class="chunk-card-text">${esc(r.texto)}</div>
      </div>
    `;
  }).join('');

  setHtml('searchResults', `
    <div class="results-meta">
      🔍 ${data.total} resultado${data.total !== 1 ? 's' : ''} para "${esc(data.query)}"
    </div>
    ${cards}
  `);
}

/* ─────────────────────────────────────────
   Multimedia (text-embedding search)
───────────────────────────────────────── */

function initMultimedia() {
  $('multimediaForm').addEventListener('submit', async e => {
    e.preventDefault();
    const query = $('multimediaQuery').value.trim();
    const limit = parseInt($('multimediaLimit').value) || 8;
    const tipo  = $('multimediaTipo').value || null;

    showLoading('multimediaResults', 'Buscando multimedia...');

    try {
      const body = { query, limit };
      if (tipo) body.tipo = tipo;
      const data = await apiPost('/multimedia/search', body);

      if (!data.results?.length) {
        return setHtml('multimediaResults', `
          <div class="empty-box">
            <div class="empty-icon">🖼️</div>
            <p>No se encontró multimedia para "<strong>${esc(data.query)}</strong>".</p>
          </div>
        `);
      }

      const cards = data.results.map(r => {
        const meta       = r.metadata || {};
        const url        = resolveUrl(r.url);
        const imgHtml    = url
          ? `<img class="media-card-img" src="${esc(url)}" alt="${esc(r.titulo || '')}" loading="lazy">`
          : `<div class="media-card-placeholder">🏞️</div>`;
        const typeBadge  = r.tipo                 ? badge(r.tipo, 'blue')             : '';
        const destBadge  = meta.nombre_destino    ? badge(meta.nombre_destino, 'slate') : '';
        const scoreBadge = r.score != null         ? badge(scoreLabel(r.score), 'score') : '';
        return `
          <div class="media-card">
            ${imgHtml}
            <div class="media-card-body">
              <div class="media-card-title" title="${esc(r.titulo)}">${esc(r.titulo)}</div>
              ${r.descripcion ? `<div class="media-card-desc">${esc(r.descripcion)}</div>` : ''}
              <div class="media-card-footer">${typeBadge}${destBadge}${scoreBadge}</div>
            </div>
          </div>
        `;
      }).join('');

      setHtml('multimediaResults', `
        <div class="results-meta">🖼️ ${data.total} resultado${data.total !== 1 ? 's' : ''}</div>
        <div class="media-grid">${cards}</div>
      `);

      $('multimediaResults').querySelectorAll('.media-card-img').forEach(img => {
        img.onerror = function () {
          const ph = document.createElement('div');
          ph.className = 'media-card-placeholder';
          ph.textContent = '🏞️';
          this.replaceWith(ph);
        };
      });

    } catch (err) {
      showError('multimediaResults', err.message);
    }
  });
}

/* ─────────────────────────────────────────
   CLIP — Text Search
───────────────────────────────────────── */

function initClipText() {
  $('clipTextForm').addEventListener('submit', async e => {
    e.preventDefault();
    const query = $('clipTextQuery').value.trim();
    const limit = parseInt($('clipTextLimit').value) || 8;

    showLoading('clipTextResults', 'Buscando imágenes con CLIP...');
    try {
      const data = await apiPost('/multimedia/text-search-clip', { query, limit });
      renderMediaGrid(data.results, 'clipTextResults');
    } catch (err) {
      showError('clipTextResults', err.message);
    }
  });
}

/* ─────────────────────────────────────────
   CLIP — Image Search
───────────────────────────────────────── */

function initClipImage() {
  initDropzone('clipImageFile', 'clipDropzone', 'clipDropzoneBody');

  $('clipImageForm').addEventListener('submit', async e => {
    e.preventDefault();
    const file  = $('clipImageFile').files[0];
    const limit = parseInt($('clipImageLimit').value) || 8;

    if (!file) return showError('clipImageResults', 'Selecciona una imagen primero.');

    const form = new FormData();
    form.append('file', file);
    form.append('limit', limit);

    showLoading('clipImageResults', 'Analizando imagen con CLIP...');
    try {
      const data = await apiFormPost('/multimedia/image-search', form);
      renderMediaGrid(data.results, 'clipImageResults');
    } catch (err) {
      showError('clipImageResults', err.message);
    }
  });
}

/* ─────────────────────────────────────────
   Multimodal Search
───────────────────────────────────────── */

function initMultimodal() {
  initDropzone('multimodalFile', 'multimodalDropzone', 'multimodalDropzoneBody');

  $('multimodalForm').addEventListener('submit', async e => {
    e.preventDefault();
    const query = $('multimodalQuery').value.trim();
    const file  = $('multimodalFile').files[0];
    const limit = parseInt($('multimodalLimit').value) || 8;

    if (!query && !file) {
      return showError('multimodalResults', 'Debes proporcionar al menos un texto o una imagen.');
    }

    const form = new FormData();
    if (query) form.append('query', query);
    if (file)  form.append('file', file);
    form.append('limit', limit);

    showLoading('multimodalResults', 'Realizando búsqueda multimodal...');
    try {
      const data = await apiFormPost('/multimodal/search', form);
      renderMediaGrid(data.results, 'multimodalResults');
    } catch (err) {
      showError('multimodalResults', err.message);
    }
  });
}

/* ─────────────────────────────────────────
   Chunking Comparison
───────────────────────────────────────── */

function initChunking() {
  $('chunkingForm').addEventListener('submit', async e => {
    e.preventDefault();
    const doc_id  = $('chunkingDocId').value.trim();
    const text    = $('chunkingText').value.trim();
    const persist = $('chunkingPersist').checked;

    const strategies = [];
    if ($('stratFixed').checked)    strategies.push('fixed-size');
    if ($('stratSentence').checked) strategies.push('sentence-aware');

    if (!strategies.length) {
      return showError('chunkingResults', 'Selecciona al menos una estrategia de chunking.');
    }

    showLoading('chunkingResults', 'Comparando estrategias de chunking...');
    try {
      const data = await apiPost('/chunking/compare', { doc_id, text, strategies, persist });
      renderChunkingResults(data);
    } catch (err) {
      showError('chunkingResults', err.message);
    }
  });
}

function renderChunkingResults(data) {
  const statsHtml = (data.stats || []).map(s => `
    <div class="stat-card">
      <div class="stat-card-title">
        ${badge(s.estrategia_chunking, s.estrategia_chunking === 'fixed-size' ? 'blue' : 'purple')}
      </div>
      <div class="stat-row"><span class="stat-key">Total de chunks</span><span class="stat-val">${s.total_chunks}</span></div>
      <div class="stat-row"><span class="stat-key">Promedio (chars)</span><span class="stat-val">${Number(s.promedio_caracteres).toFixed(0)}</span></div>
      <div class="stat-row"><span class="stat-key">Mínimo (chars)</span><span class="stat-val">${s.minimo_caracteres}</span></div>
      <div class="stat-row"><span class="stat-key">Máximo (chars)</span><span class="stat-val">${s.maximo_caracteres}</span></div>
    </div>
  `).join('');

  const previewsHtml = (data.previews || []).map(p => `
    <div class="preview-card">
      <div class="preview-card-meta">
        ${badge(p.estrategia_chunking, p.estrategia_chunking === 'fixed-size' ? 'blue' : 'purple')}
        ${badge(`#${p.chunk_index}`, 'slate')}
        ${badge(`${p.caracteres} chars`, 'green')}
      </div>
      <div class="preview-card-text">${esc(p.chunk_texto)}</div>
    </div>
  `).join('');

  const persistBadge = data.persisted
    ? `${badge('✓ Guardado en BD', 'green')}`
    : '';

  setHtml('chunkingResults', `
    <div class="results-meta">⚙️ doc_id: ${esc(data.doc_id)} ${persistBadge}</div>
    <div class="chunking-stats">${statsHtml}</div>
    <div class="section-label">Vista previa de fragmentos</div>
    <div class="preview-grid">${previewsHtml}</div>
  `);
}

/* ─────────────────────────────────────────
   Bootstrap
───────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  initTabs();
  initRag();
  initSearch();
  initMultimedia();
  initClipText();
  initClipImage();
  initMultimodal();
  initChunking();
});
