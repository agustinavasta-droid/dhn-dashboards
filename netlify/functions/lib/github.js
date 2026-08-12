import { buildHtml } from './build-html.js';

const OWNER = 'agustinavasta-droid';
const REPO = 'dhn-dashboards';
const BRANCH = 'main';
const FILE_PATH = 'index.html';
const API = 'https://api.github.com';

function headers() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error('Falta configurar GITHUB_TOKEN en Netlify.');
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
  };
}

async function ghFetch(path, options = {}) {
  const resp = await fetch(`${API}${path}`, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`GitHub API ${options.method || 'GET'} ${path} -> ${resp.status}: ${body.slice(0, 300)}`);
  }
  return resp.json();
}

// Trae el commit/tree/blob actuales de index.html en la rama main y extrae
// el DATA embebido (mismo formato que cargar_empresas_previas() en Python),
// para poder mergear solo la empresa que se está subiendo y conservar la
// otra tal cual.
async function leerEstadoActual() {
  const ref = await ghFetch(`/repos/${OWNER}/${REPO}/git/ref/heads/${BRANCH}`);
  const commitSha = ref.object.sha;
  const commit = await ghFetch(`/repos/${OWNER}/${REPO}/git/commits/${commitSha}`);
  const treeSha = commit.tree.sha;
  const tree = await ghFetch(`/repos/${OWNER}/${REPO}/git/trees/${treeSha}`);
  const entry = tree.tree.find((e) => e.path === FILE_PATH);
  if (!entry) throw new Error(`No se encontró ${FILE_PATH} en el repo.`);
  const blob = await ghFetch(`/repos/${OWNER}/${REPO}/git/blobs/${entry.sha}`);
  const html = Buffer.from(blob.content, 'base64').toString('utf-8');

  const m = html.match(/const DATA\s*=\s*(\{.*?\});\n/s);
  let empresas = {};
  if (m) {
    try { empresas = JSON.parse(m[1]); } catch { empresas = {}; }
  }
  return { empresas, commitSha, treeSha };
}

// `empresaKey` es la empresa que se está actualizando ('dhn'|'deli') y
// `datosEmpresa` su nuevo bloque {label, clientes, totales}. Si hay que
// reintentar por una carrera (alguien commiteó en el medio, p.ej. DHN y
// Deli subidos casi a la vez), se vuelve a leer el estado y se reaplica
// SOLO el cambio de esta empresa sobre los datos más nuevos, para no pisar
// lo que haya cambiado la otra mientras tanto.
async function commitNuevoIndex(empresaKey, datosEmpresa, mensaje, estado, intento = 0) {
  const empresas = { ...estado.empresas, [empresaKey]: datosEmpresa };
  const html = buildHtml(empresas);

  const blob = await ghFetch(`/repos/${OWNER}/${REPO}/git/blobs`, {
    method: 'POST',
    body: JSON.stringify({ content: html, encoding: 'utf-8' }),
  });

  const tree = await ghFetch(`/repos/${OWNER}/${REPO}/git/trees`, {
    method: 'POST',
    body: JSON.stringify({
      base_tree: estado.treeSha,
      tree: [{ path: FILE_PATH, mode: '100644', type: 'blob', sha: blob.sha }],
    }),
  });

  const commit = await ghFetch(`/repos/${OWNER}/${REPO}/git/commits`, {
    method: 'POST',
    body: JSON.stringify({ message: mensaje, tree: tree.sha, parents: [estado.commitSha] }),
  });

  const refResp = await fetch(`${API}/repos/${OWNER}/${REPO}/git/refs/heads/${BRANCH}`, {
    method: 'PATCH',
    headers: headers(),
    body: JSON.stringify({ sha: commit.sha, force: false }),
  });

  if (!refResp.ok) {
    // Alguien commiteó en el medio (carrera entre DHN y Deli subidos casi
    // a la vez, o con un push manual). Se reintenta una vez sobre el estado
    // más nuevo antes de rendirse.
    if (intento === 0) {
      const nuevoEstado = await leerEstadoActual();
      return commitNuevoIndex(empresaKey, datosEmpresa, mensaje, nuevoEstado, 1);
    }
    const body = await refResp.text().catch(() => '');
    throw new Error(`No se pudo actualizar la rama (conflicto): ${body.slice(0, 300)}`);
  }

  return { commitSha: commit.sha };
}

export { leerEstadoActual, commitNuevoIndex };
