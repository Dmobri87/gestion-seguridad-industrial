# Guía de Despliegue - Sistema de Gestión de Seguridad Industrial

## Guías rápidas relacionadas

- Ejecución local sin Docker: `LOCAL_SETUP.md`
- Checklist de producción: `PRODUCTION_CHECKLIST.md`

## 1. Requisitos del Sistema

### Backend
- Python 3.10+
- pip (gestor de paquetes)

### Frontend
- Node.js 18+
- npm 9+

### Base de Datos (Producción)
- PostgreSQL 14+ (recomendado)
- MySQL 8+ (alternativa)

---

## 2. Configuración de Desarrollo

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python init_db.py
python create_test_users.py
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

**URLs de Desarrollo:**
- Frontend: http://localhost:5173 o http://localhost:3001
- Backend API: http://localhost:8000
- Documentación API: http://localhost:8000/docs

---

## 3. Credenciales de Prueba

| Rol | Email | Contraseña | Permisos |
|-----|-------|------------|----------|
| **Administrador** | admin@empresa.com | admin123 | Acceso total |
| **Coordinador** | coordinador@empresa.com | coord123 | Crear planes, aprobar |
| **Supervisor** | supervisor@empresa.com | super123 | Aprobar ejecuciones |
| **TAE 1** | tae1@empresa.com | tae123 | Registrar ejecuciones |
| **TAE 2** | tae2@empresa.com | tae123 | Registrar ejecuciones |
| **TAE 3** | tae3@empresa.com | tae123 | Registrar ejecuciones |
| **Paramédico** | paramedico@empresa.com | para123 | Atender emergencias |

---

## 4. Despliegue en Producción

### 4.1 Variables de Entorno

Crear archivo `.env` en `/backend`:

```env
# Base de datos PostgreSQL
DATABASE_URL=postgresql://usuario:password@host:5432/gestion_seguridad

# Seguridad
SECRET_KEY=tu-clave-secreta-muy-larga-y-segura-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (dominios permitidos)
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# Modo producción
DEBUG=False
```

### 4.2 Compilar Frontend para Producción

```bash
cd frontend
npm run build
```

Esto genera la carpeta `dist/` con los archivos estáticos.

### 4.3 Opciones de Hosting

#### Opción A: Railway (Recomendado para empezar)
1. Crear cuenta en [railway.app](https://railway.app)
2. Conectar repositorio de GitHub
3. Agregar servicio PostgreSQL
4. Configurar variables de entorno
5. Deploy automático

**Estimado:** ~$5-10/mes

#### Opción B: DigitalOcean App Platform
1. Crear cuenta en [digitalocean.com](https://digitalocean.com)
2. Crear App desde repositorio
3. Agregar base de datos PostgreSQL
4. Configurar variables de entorno

**Estimado:** ~$12-20/mes

#### Opción C: AWS (Escalable)
1. **EC2** para backend (Gunicorn + Nginx)
2. **RDS** para PostgreSQL
3. **S3 + CloudFront** para frontend estático
4. **Route 53** para dominio

**Estimado:** ~$30-50/mes (puede variar)

#### Opción D: VPS (Económico)
1. Alquilar VPS (Contabo, Hetzner, OVH)
2. Instalar Docker
3. Usar docker-compose

**Estimado:** ~$5-10/mes

---

## 5. Docker (Producción)

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: gestion_seguridad
      POSTGRES_USER: gsuser
      POSTGRES_PASSWORD: gspassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://gsuser:gspassword@db:5432/gestion_seguridad
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
```

### Dockerfile Backend (`backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### Dockerfile Frontend (`frontend/Dockerfile`)

```dockerfile
FROM node:18 as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### nginx.conf (`frontend/nginx.conf`)

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 6. Comandos Docker

```bash
# Construir e iniciar
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Reiniciar
docker-compose restart

# Ejecutar migraciones
docker-compose exec backend python init_db.py
```

---

## 7. Checklist Pre-Producción

- [ ] Cambiar SECRET_KEY por una clave segura
- [ ] Configurar HTTPS (Let's Encrypt)
- [ ] Configurar backups automáticos de BD
- [ ] Cambiar contraseñas de usuarios por defecto
- [ ] Configurar logs de auditoría
- [ ] Configurar monitoreo (Sentry, New Relic)
- [ ] Configurar CDN para archivos estáticos
- [ ] Pruebas de carga
- [ ] Revisar permisos de archivos

---

## 8. Soporte

Para reportar bugs o solicitar funcionalidades:
- Crear issue en el repositorio
- Email: soporte@tuempresa.com

---

## 9. Licencia

Sistema desarrollado para gestión interna de seguridad industrial.
Todos los derechos reservados.
