#!/usr/bin/env bash
set -euo pipefail

# Deploy para OCI usando compose base + override seguro.
# Ejecutar en la VM como usuario deploy, dentro del repo:
#   bash scripts/oci/deploy.sh

if [[ ! -f ".env" ]]; then
  echo "ERROR: .env not found. Create it from .env.production.template"
  exit 1
fi

echo "[1/5] Validating compose"
docker compose -f docker-compose.yml -f docker-compose.oci.yml config --quiet

echo "[2/5] Build images"
docker compose -f docker-compose.yml -f docker-compose.oci.yml build

echo "[3/5] Start services"
docker compose -f docker-compose.yml -f docker-compose.oci.yml up -d

echo "[4/5] Running containers"
docker compose -f docker-compose.yml -f docker-compose.oci.yml ps

echo "[5/5] Health checks"
echo "Backend health:"
curl -fsS http://localhost:8000/health || true
echo
echo "Frontend check:"
curl -I http://localhost || true

echo "Deploy completed."
