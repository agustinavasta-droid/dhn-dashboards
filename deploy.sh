#!/usr/bin/env bash
# Publica index.html en Netlify (sitio dhn-dashboards).
# Correr después de `python actualizar.py ...`, una vez que index.html esté listo.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env.netlify ]; then
  echo "❌ Falta .env.netlify con NETLIFY_AUTH_TOKEN y NETLIFY_SITE_ID"
  exit 1
fi
source .env.netlify

if [ ! -f index.html ]; then
  echo "❌ No existe index.html. Corré primero: python actualizar.py ..."
  exit 1
fi

rm -rf .deploy_tmp
mkdir .deploy_tmp
cp index.html .deploy_tmp/

netlify deploy --prod --dir=.deploy_tmp --site="$NETLIFY_SITE_ID" --auth="$NETLIFY_AUTH_TOKEN"

rm -rf .deploy_tmp
