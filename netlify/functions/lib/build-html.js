import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// El mismo template.html que usa build_pdf_grid.py (fuente única para no
// duplicar/desincronizar el HTML entre el flujo CLI y el flujo web). Netlify
// empaqueta las funciones como CJS (aunque el repo declare "type":"module"),
// donde `import.meta.url` queda vacío pero `__dirname` sí lo define esbuild
// correctamente — de ahí el `typeof` guard, es el único chequeo seguro para
// una variable que puede no existir según el formato de salida. Se prueban
// varias ubicaciones porque el empaquetado a veces deja los archivos de
// netlify/functions/lib/ en su ruta anidada original (junto al repo, con
// template.html tres niveles arriba) y a veces los deja todos al lado del
// entrypoint (junto a template.html, por `included_files`).
function resolveTemplatePath() {
  // eslint-disable-next-line no-undef
  const here = typeof __dirname !== 'undefined'
    ? __dirname
    : path.dirname(fileURLToPath(import.meta.url));
  const candidatos = [
    path.join(here, 'template.html'),
    path.join(here, '..', '..', '..', 'template.html'),
    path.join(here, '..', '..', 'template.html'),
  ];
  const found = candidatos.find((p) => existsSync(p));
  if (!found) throw new Error('No se encontró template.html');
  return found;
}

function buildHtml(empresas) {
  const template = readFileSync(resolveTemplatePath(), 'utf-8');
  const dataJson = JSON.stringify(empresas);
  return template.replace('__DATA_JSON__', dataJson);
}

export { buildHtml };
