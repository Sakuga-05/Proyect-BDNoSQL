const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const API_BASE_KEY = "proyect_bdnosql_api_base";

export function getApiBase() {
  return localStorage.getItem(API_BASE_KEY) || DEFAULT_API_BASE;
}

export function setApiBase(value) {
  const clean = value.trim().replace(/\/$/, "");
  localStorage.setItem(API_BASE_KEY, clean || DEFAULT_API_BASE);
  return getApiBase();
}

export function assetUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${getApiBase()}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof body === "object" ? body.detail || JSON.stringify(body) : body;
    throw new Error(detail || `Error HTTP ${response.status}`);
  }
  return body;
}

async function request(path, options = {}) {
  const response = await fetch(`${getApiBase()}${path}`, options);
  return parseResponse(response);
}

export const Api = {
  health: () => request("/health"),
  stats: () => request("/catalog/stats"),
  list: (collection, limit = 100, skip = 0) =>
    request(`/catalog/${collection}?limit=${limit}&skip=${skip}`),
  detail: (collection, id) => request(`/catalog/${collection}/${id}`),
  searchText: (payload) =>
    request("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  rag: (payload) =>
    request("/rag", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  multimediaSearch: (payload) =>
    request("/multimedia/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  clipTextSearch: (payload) =>
    request("/multimedia/text-search-clip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  clipImageSearch: (file, limit = 8) => {
    const form = new FormData();
    form.append("file", file);
    form.append("limit", limit);
    return request("/multimedia/image-search", { method: "POST", body: form });
  },
  multimodalSearch: ({ query, file, limit = 8 }) => {
    const form = new FormData();
    if (query) form.append("query", query);
    if (file) form.append("file", file);
    form.append("limit", limit);
    return request("/multimodal/search", { method: "POST", body: form });
  },
  compareChunking: (payload) =>
    request("/chunking/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
