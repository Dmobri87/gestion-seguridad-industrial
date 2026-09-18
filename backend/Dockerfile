# =============================================================================
# Dockerfile - Backend FastAPI
# Sistema de Gestion de Seguridad Industrial
# =============================================================================

FROM python:3.11-slim

# Crear usuario no-root para seguridad
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar codigo de la aplicacion
COPY --chown=appuser:appgroup . .

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /app/uploads /app/logs \
    && chown -R appuser:appgroup /app/uploads /app/logs

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
