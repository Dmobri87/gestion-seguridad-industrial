# Usar imagen base de Python optimizada
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /code

# Instalar dependencias del sistema necesarias para PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de dependencias
COPY requirements.txt /code/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar el código de la aplicación
COPY ./app /code/app

# Exponer el puerto
EXPOSE 80

# Comando por defecto (se puede sobrescribir en docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]