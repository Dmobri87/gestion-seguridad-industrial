#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo " Gestión GAE — Inicio en Producción"
echo "========================================"

# 1. Verificar .env existe
if [ ! -f ".env" ]; then
  echo "❌ ERROR: Archivo .env no encontrado en la raíz del proyecto"
  exit 1
fi

# 2. Verificar SECRET_KEY tiene longitud suficiente
SECRET_KEY_LEN=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2- | wc -c)
if [ "$SECRET_KEY_LEN" -lt 64 ]; then
  echo "❌ ERROR: SECRET_KEY demasiado corta (mínimo 64 caracteres)"
  exit 1
fi
echo "✅ SECRET_KEY: longitud OK ($SECRET_KEY_LEN chars)"

# 3. Verificar DEBUG=False
DEBUG_VALUE=$(grep "^DEBUG=" .env | cut -d'=' -f2-)
if [ "$DEBUG_VALUE" != "False" ]; then
  echo "❌ ERROR: DEBUG debe ser 'False' en producción (actual: $DEBUG_VALUE)"
  exit 1
fi
echo "✅ DEBUG=False"

# 4. Verificar CORS_ORIGINS no apunta solo a localhost
CORS_VALUE=$(grep "^CORS_ORIGINS=" .env | cut -d'=' -f2-)
if echo "$CORS_VALUE" | grep -q "localhost" && ! echo "$CORS_VALUE" | grep -qv "localhost"; then
  echo "⚠️  ADVERTENCIA: CORS_ORIGINS solo contiene localhost — ¿olvidaste el dominio de producción?"
fi
echo "✅ CORS_ORIGINS: $CORS_VALUE"

# 5. Validar sintaxis Python del backend
echo " Validando sintaxis Python..."
python -m py_compile backend/app/main.py && echo "✅ main.py OK"
python -m py_compile backend/app/api/v1/endpoints/certifications.py && echo "✅ certifications.py OK"
python -m py_compile backend/app/api/v1/endpoints/executions.py && echo "✅ executions.py OK"

# 6. Validar docker-compose
echo " Validando docker-compose.yml..."
docker compose config --quiet && echo "✅ docker-compose.yml válido"

# 7. Build y arranque
echo ""
echo " Construyendo imágenes y arrancando servicios..."
docker compose build --no-cache
docker compose up -d

echo ""
echo "========================================"
echo " ✅ Servicios arrancados correctamente"
echo " Frontend: http://localhost (nginx)"
echo " Backend:  http://localhost/api/v1/docs"
echo " Logs:     docker compose logs -f"
echo "========================================"
