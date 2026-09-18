#!/usr/bin/env bash
set -euo pipefail

# Update de release en OCI.
# Ejecutar en VM dentro del repo:
#   bash scripts/oci/update.sh

BRANCH="${BRANCH:-main}"

echo "[1/4] Fetch latest code"
git fetch --all --prune
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

echo "[2/4] Rebuild + restart"
docker compose -f docker-compose.yml -f docker-compose.oci.yml up -d --build

echo "[3/4] Status"
docker compose -f docker-compose.yml -f docker-compose.oci.yml ps

echo "[4/4] Tail logs (last 60 lines)"
docker compose -f docker-compose.yml -f docker-compose.oci.yml logs --tail=60 backend frontend

echo "Update completed."
