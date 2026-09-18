# :shield: Sistema de Gestion de Seguridad Industrial y Salud Ocupacional

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## :page_facing_up: Tabla de Contenidos

- [Descripcion](#-descripcion)
- [Caracteristicas Principales](#-caracteristicas-principales)
- [Tecnologias](#-tecnologias)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalacion y Desarrollo Local](#-instalacion-y-desarrollo-local)
- [Despliegue en Produccion](#-despliegue-en-produccion)
- [Variables de Entorno](#-variables-de-entorno)
- [SSL / HTTPS](#-ssl--https)
- [Backup y Restauracion](#-backup-y-restauracion)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Seguridad](#-seguridad)
- [Licencia](#-licencia)
- [Autor](#-autor)

---

## :memo: Descripcion

Sistema empresarial integral para la **gestion de seguridad industrial y salud ocupacional**. Permite administrar de forma centralizada todos los procesos criticos de seguridad en una organizacion:

- **Grupos de trabajo** y estructura organizacional
- **Gestion de usuarios** con roles diferenciados y permisos granulares
- **Planificacion y ejecucion** de actividades de seguridad
- **Inspecciones** y seguimiento de cumplimiento normativo
- **Certificaciones** del personal y control de vencimientos
- **Gestion de equipos** de seguridad y proteccion
- **Respuesta a emergencias** con registro y seguimiento
- **Ciclos de planificacion (3 por mes)** con metricas de avance y cumplimiento
- **Dashboard ejecutivo** con KPIs y metricas en tiempo real

---

## :star: Caracteristicas Principales

| Modulo | Descripcion |
|---|---|
| :bar_chart: **Dashboard** | Panel ejecutivo con KPIs, metricas de cumplimiento y graficos interactivos |
| :busts_in_silhouette: **Gestion de Usuarios** | CRUD completo con 8 roles: Administrador, Coordinador, Supervisor, TAE, PSE, Paramedico, Empleado, Invitado |
| :office: **Grupos de Trabajo** | Organizacion de equipos, asignacion de responsabilidades y estructura jerarquica |
| :calendar: **Planificacion** | Plan mensual en 3 ciclos con asignacion de actividades, responsables y fechas limite |
| :clipboard: **Actividades** | Registro, seguimiento y ejecucion de actividades con evidencia requerida por defecto (exceptuable por coordinador/admin) |
| :wrench: **Equipos** | Control de inventario, mantenimiento y estado de equipos de seguridad |
| :rotating_light: **Emergencias** | Registro de incidentes, respuesta y seguimiento de emergencias |
| :mortar_board: **Certificaciones** | Gestion de certificaciones del personal con alertas de vencimiento |
| :closed_lock_with_key: **Autenticacion 2FA** | Verificacion en dos pasos mediante OTP enviado por correo electronico |
| :shield: **Control de Acceso** | Control de acceso basado en roles (RBAC) con permisos granulares por endpoint |

---

## :computer: Tecnologias

### Backend

| Tecnologia | Version | Proposito |
|---|---|---|
| [Python](https://www.python.org) | 3.11+ | Lenguaje principal |
| [FastAPI](https://fastapi.tiangolo.com) | Latest | Framework web asincrono |
| [SQLAlchemy](https://www.sqlalchemy.org) | Latest | ORM para base de datos |
| [Alembic](https://alembic.sqlalchemy.org) | Latest | Migraciones de base de datos |
| [PostgreSQL](https://www.postgresql.org) | 15 | Base de datos en produccion |
| [SQLite](https://www.sqlite.org) | - | Base de datos en desarrollo |
| [Redis](https://redis.io) | 7 | Cache y rate limiting |
| [bcrypt](https://github.com/pyca/bcrypt) | 4.0.1 | Hash de contrasenas |
| [python-jose](https://github.com/mpdavis/python-jose) | Latest | Tokens JWT |
| [Gunicorn](https://gunicorn.org) | Latest | Servidor WSGI produccion |

### Frontend

| Tecnologia | Version | Proposito |
|---|---|---|
| [React](https://react.dev) | 18.2 | Libreria de interfaz de usuario |
| [TypeScript](https://www.typescriptlang.org) | 5.3 | Tipado estatico |
| [Vite](https://vitejs.dev) | 5.0 | Build tool y dev server |
| [Ant Design](https://ant.design) | 5.12 | Componentes de UI empresarial |
| [Zustand](https://github.com/pmndrs/zustand) | 4.4 | Gestion de estado global |
| [Axios](https://axios-http.com) | 1.6 | Cliente HTTP |
| [Ant Design Charts](https://charts.ant.design) | 2.0 | Graficos y visualizaciones |
| [React Router](https://reactrouter.com) | 6.21 | Enrutamiento SPA |
| [Tailwind CSS](https://tailwindcss.com) | 3.4 | Utilidades CSS |
| [Day.js](https://day.js.org) | 1.11 | Manejo de fechas |

### Infraestructura

| Tecnologia | Proposito |
|---|---|
| [Docker](https://www.docker.com) | Contenedorizacion de servicios |
| [Docker Compose](https://docs.docker.com/compose/) | Orquestacion multi-contenedor |
| [Nginx](https://nginx.org) | Reverse proxy, servidor de archivos estaticos y SSL termination |
| [Let's Encrypt](https://letsencrypt.org) | Certificados SSL/TLS gratuitos |
| [GitHub Actions](https://github.com/features/actions) | CI/CD pipeline automatizado |
| [GHCR](https://ghcr.io) | GitHub Container Registry para imagenes Docker |

---

## :open_file_folder: Estructura del Proyecto

```
gestion_proyectos/
|
|-- backend/                          # API Backend (FastAPI)
|   |-- app/
|   |   |-- api/
|   |   |   |-- v1/
|   |   |       |-- endpoints/
|   |   |           |-- auth.py               # Autenticacion y 2FA
|   |   |           |-- organizations.py      # Organizaciones
|   |   |           |-- dashboard.py          # Dashboard y KPIs
|   |   |           |-- emergencies.py        # Gestion de emergencias
|   |   |           |-- certifications.py     # Certificaciones
|   |   |           |-- work_groups.py        # Grupos de trabajo
|   |   |           |-- planning.py           # Ciclos de planificacion
|   |   |           |-- activity_categories.py # Categorias de actividades
|   |   |           |-- activity_templates.py  # Plantillas de actividades
|   |   |           |-- users.py              # Gestion de usuarios (legacy)
|   |   |-- core/
|   |   |   |-- config.py            # Configuracion centralizada
|   |   |   |-- database.py          # Conexion a base de datos
|   |   |   |-- security.py          # JWT, hashing, autenticacion
|   |   |   |-- dependencies.py      # Dependencias de inyeccion
|   |   |   |-- email.py             # Servicio de envio de correos
|   |   |   |-- logging_config.py    # Configuracion de logging
|   |   |-- middleware/
|   |   |   |-- request_logging.py   # Middleware de logging de peticiones
|   |   |-- models/
|   |   |   |-- user.py              # Modelo de usuarios
|   |   |   |-- organization.py      # Organizaciones
|   |   |   |-- work_group.py        # Grupos de trabajo
|   |   |   |-- department.py        # Departamentos
|   |   |   |-- activity.py          # Actividades
|   |   |   |-- activity_category.py # Categorias de actividades
|   |   |   |-- activity_assignment.py # Asignaciones
|   |   |   |-- planning.py          # Planificacion
|   |   |   |-- execution.py         # Ejecuciones
|   |   |   |-- compliance.py        # Cumplimiento
|   |   |   |-- equipment.py         # Equipos de seguridad
|   |   |   |-- certification.py     # Certificaciones
|   |   |   |-- emergency.py         # Emergencias
|   |   |   |-- program.py           # Programas
|   |   |-- routes/                   # Rutas legacy
|   |   |-- schemas/                  # Esquemas Pydantic
|   |   |-- db/
|   |   |   |-- init_db.py           # Inicializacion de BD
|   |   |   |-- seed_data.py         # Datos semilla
|   |   |-- main.py                  # Punto de entrada de la aplicacion
|   |-- alembic.ini                   # Configuracion de Alembic
|   |-- Dockerfile                    # Imagen Docker del backend
|   |-- .dockerignore
|   |-- requirements.txt              # Dependencias Python
|
|-- frontend/                         # Aplicacion Frontend (React)
|   |-- src/
|   |   |-- pages/
|   |   |   |-- auth/
|   |   |   |   |-- LoginPage.tsx     # Pagina de inicio de sesion
|   |   |   |-- dashboard/
|   |   |   |   |-- DashboardPage.tsx # Dashboard principal
|   |   |   |-- admin/
|   |   |   |   |-- AdminPage.tsx     # Panel de administracion
|   |   |   |-- activities/
|   |   |   |   |-- ActivitiesPage.tsx # Gestion de actividades
|   |   |   |-- planning/
|   |   |   |   |-- PlanningListPage.tsx   # Lista de planificaciones
|   |   |   |   |-- PlanningDetailPage.tsx # Detalle de planificacion
|   |   |   |-- execution/
|   |   |   |   |-- ExecutionPage.tsx # Ejecucion de actividades
|   |   |   |-- equipment/
|   |   |   |   |-- EquipmentPage.tsx # Gestion de equipos
|   |   |   |-- emergencies/
|   |   |   |   |-- EmergenciesPage.tsx # Gestion de emergencias
|   |   |   |-- certifications/
|   |   |   |   |-- CertificationsPage.tsx # Certificaciones
|   |   |   |-- users/
|   |   |   |   |-- UsersPerformancePage.tsx # Rendimiento de usuarios
|   |   |   |-- profile/
|   |   |       |-- ProfilePage.tsx   # Perfil de usuario
|   |   |-- layouts/
|   |   |   |-- MainLayout.tsx        # Layout principal
|   |   |-- stores/
|   |   |   |-- authStore.ts          # Estado de autenticacion (Zustand)
|   |   |-- services/
|   |   |   |-- api.ts                # Cliente API (Axios)
|   |   |-- types/
|   |   |   |-- index.ts              # Tipos TypeScript
|   |   |-- App.tsx                    # Componente raiz y rutas
|   |   |-- main.tsx                   # Punto de entrada
|   |   |-- index.css                  # Estilos globales
|   |-- Dockerfile                     # Build multi-stage (Node + Nginx)
|   |-- nginx.conf                     # Configuracion Nginx desarrollo
|   |-- package.json
|
|-- nginx/
|   |-- nginx.prod.conf               # Configuracion Nginx produccion (SSL)
|
|-- scripts/
|   |-- init-letsencrypt.sh           # Inicializacion de certificados SSL
|   |-- renew-ssl.sh                  # Renovacion de certificados SSL
|   |-- backup-db.sh                  # Backup de base de datos
|   |-- restore-db.sh                 # Restauracion de base de datos
|
|-- .github/
|   |-- workflows/
|       |-- ci-cd.yml                 # Pipeline CI/CD
|
|-- docker-compose.yml                # Compose produccion
|-- docker-compose.dev.yml            # Compose desarrollo (override)
|-- docker-compose.backup.yml         # Compose servicio de backup
|-- .env.production.template          # Plantilla de variables de entorno
|-- .gitignore
```

---

## :white_check_mark: Requisitos Previos

### Para desarrollo local

| Requisito | Version minima | Verificar instalacion |
|---|---|---|
| **Git** | 2.x | `git --version` |
| **Python** | 3.11+ | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 9+ | `npm --version` |

### Para despliegue con Docker

| Requisito | Version minima | Verificar instalacion |
|---|---|---|
| **Docker** | 24+ | `docker --version` |
| **Docker Compose** | 2.x | `docker compose version` |

---

## :rocket: Instalacion y Desarrollo Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/gestion_proyectos.git
cd gestion_proyectos
```

### 2. Configurar variables de entorno

```bash
cp .env.production.template .env
```

Editar el archivo `.env` con los valores de desarrollo. Para desarrollo local con SQLite, los valores por defecto suelen ser suficientes.

### 3. Instalar y ejecutar el Backend

```bash
# Crear entorno virtual
cd backend
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
uvicorn app.main:app --reload --port 8002
```

El backend estara disponible en: **http://localhost:8002**
Documentacion Swagger UI: **http://localhost:8002/docs**
Documentacion ReDoc: **http://localhost:8002/redoc**

### 4. Instalar y ejecutar el Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

El frontend estara disponible en: **http://localhost:3000**

### 5. Desarrollo con Docker Compose (alternativa)

Si se prefiere usar Docker para el desarrollo local:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Esto levanta todos los servicios con hot-reload habilitado:

| Servicio | URL | Descripcion |
|---|---|---|
| Frontend | http://localhost:3000 | Vite dev server con HMR |
| Backend | http://localhost:8002 | FastAPI con auto-reload |
| PostgreSQL | localhost:5432 | Accesible para pgAdmin/DBeaver |
| Redis | localhost:6379 | Accesible para inspeccion local |

---

## :package: Despliegue en Produccion

### Con Docker Compose

#### 1. Preparar el servidor

Asegurar que Docker y Docker Compose estan instalados en el servidor de produccion.

#### 2. Configurar variables de entorno

```bash
cp .env.production.template .env
chmod 600 .env
```

Editar `.env` y reemplazar **TODOS** los valores marcados con `CHANGE_ME` o `your-*`.

> :warning: **IMPORTANTE**: Nunca subir el archivo `.env` al repositorio. El archivo `.gitignore` ya incluye esta exclusion.

#### 3. Generar clave secreta

```bash
openssl rand -base64 64
```

Copiar el resultado en la variable `SECRET_KEY` del archivo `.env`.

#### 4. Iniciar los servicios

```bash
docker-compose up -d --build
```

#### 5. Verificar que los servicios estan corriendo

```bash
docker-compose ps
docker-compose logs -f
```

#### 6. Inicializar certificados SSL

```bash
sudo bash scripts/init-letsencrypt.sh tudominio.com tu-email@ejemplo.com
```

#### 7. Health check

```bash
curl -s http://localhost:8000/health
```

---

## :gear: Variables de Entorno

Archivo de referencia: `.env.production.template`

### Base de Datos

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexion completa a PostgreSQL | `postgresql://seguridad_user:PASSWORD@db:5432/seguridad_industrial` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `seguridad_user` |
| `POSTGRES_PASSWORD` | Contrasena de PostgreSQL | *(generar contrasena segura)* |
| `POSTGRES_DB` | Nombre de la base de datos | `seguridad_industrial` |
| `POSTGRES_HOST` | Host de la base de datos | `db` |
| `POSTGRES_PORT` | Puerto de la base de datos | `5432` |

### Seguridad

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta para firmar tokens JWT | *(generar con `openssl rand -base64 64`)* |
| `ALGORITHM` | Algoritmo de firmado JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tiempo de expiracion del token en minutos | `30` |
| `DEBUG` | Modo debug (deshabilitar en produccion) | `False` |

### CORS

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `CORS_ORIGINS` | Origenes permitidos (separados por coma) | `https://tudominio.com` |

### SMTP (Correo electronico para 2FA)

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `SMTP_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Puerto SMTP | `587` |
| `SMTP_USER` | Usuario SMTP | `tu-email@gmail.com` |
| `SMTP_PASSWORD` | Contrasena de aplicacion SMTP | *(contrasena de aplicacion de Gmail)* |
| `SMTP_FROM` | Direccion del remitente | `noreply@tudominio.com` |

### Dominio y Aplicacion

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `DOMAIN` | Dominio de produccion | `tudominio.com` |
| `APP_NAME` | Nombre de la aplicacion | `Sistema de Gestion Enterprise` |
| `APP_VERSION` | Version de la aplicacion | `2.0.0` |

### Redis

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `REDIS_URL` | URL de conexion a Redis | `redis://redis:6379/0` |

### Almacenamiento (futuro)

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `MINIO_ROOT_USER` | Usuario de MinIO *(proximamente)* | `minio_user` |
| `MINIO_ROOT_PASSWORD` | Contrasena de MinIO *(proximamente)* | *(generar contrasena segura)* |
| `MINIO_ENDPOINT` | Endpoint de MinIO *(proximamente)* | `minio:9000` |

---

## :lock: SSL / HTTPS

### Obtencion de certificados con Let's Encrypt

El proyecto incluye un script automatizado para obtener certificados SSL gratuitos de Let's Encrypt:

```bash
# Inicializar certificados (primera vez)
sudo bash scripts/init-letsencrypt.sh tudominio.com admin@tudominio.com
```

El script realiza los siguientes pasos:
1. Crea los directorios necesarios
2. Genera un certificado autofirmado temporal (para que Nginx pueda arrancar)
3. Solicita el certificado real a Let's Encrypt via desafio ACME
4. Configura la renovacion automatica via cron

### Renovacion automatica

La renovacion se configura automaticamente con un cron job que se ejecuta cada 12 horas:

```
0 */12 * * * certbot renew --quiet --deploy-hook 'nginx -s reload'
```

Para renovar manualmente:

```bash
sudo bash scripts/renew-ssl.sh
```

### Requisitos para SSL

- El dominio debe apuntar a la IP del servidor (registro DNS tipo A)
- El puerto 80 debe estar abierto y accesible desde Internet
- El puerto 443 debe estar abierto y accesible desde Internet
- Nginx debe estar ejecutandose

### Configuracion de Nginx

La configuracion de produccion (`nginx/nginx.prod.conf`) incluye:

- Redireccion automatica HTTP -> HTTPS
- TLS 1.2 y TLS 1.3
- HSTS (Strict Transport Security)
- OCSP Stapling
- Rate limiting por zona (general, API, autenticacion, uploads)
- Compresion Gzip
- Headers de seguridad
- Cache agresivo para assets estaticos (1 anio con content-hash)
- Soporte para WebSocket

> :pencil: **Nota**: Reemplazar `YOUR_DOMAIN` en `nginx/nginx.prod.conf` con el dominio real antes de desplegar.

---

## :floppy_disk: Backup y Restauracion

### Backup manual

```bash
# Usando Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.backup.yml run backup
```

El backup se almacena comprimido con gzip en el volumen `backup_data` con el formato: `db_YYYY-MM-DD_HH-MM-SS.sql.gz`

### Backup automatico (cron)

Iniciar el servicio de backup con programacion automatica diaria (por defecto a las 2:00 AM):

```bash
docker-compose -f docker-compose.yml -f docker-compose.backup.yml up -d backup
```

Para cambiar la hora del backup, configurar la variable de entorno `BACKUP_CRON`:

```bash
# Ejemplo: backup a las 3:30 AM
BACKUP_CRON="30 3 * * *" docker-compose -f docker-compose.yml -f docker-compose.backup.yml up -d backup
```

### Listar backups disponibles

```bash
docker-compose -f docker-compose.yml -f docker-compose.backup.yml run backup ls -lht /backups/
```

### Restauracion

```bash
docker-compose -f docker-compose.yml -f docker-compose.backup.yml run backup \
  /scripts/restore-db.sh db_2025-01-15_10-30-00.sql.gz
```

> :warning: **ATENCION**: La restauracion **SOBREESCRIBE** la base de datos actual. Esta accion no se puede deshacer. El script solicita confirmacion antes de proceder.

### Retencion

Por defecto, se conservan los ultimos **30 backups**. Los backups mas antiguos se eliminan automaticamente. Este valor se puede ajustar con la variable `BACKUP_RETENTION`.

### Bases de datos soportadas

Los scripts de backup y restauracion soportan:
- **PostgreSQL** (produccion): utiliza `pg_dump` y `psql`
- **SQLite** (desarrollo): utiliza el comando `.backup` de SQLite

---

## :arrows_counterclockwise: CI/CD Pipeline

El proyecto utiliza **GitHub Actions** para integracion y despliegue continuo. El pipeline se define en `.github/workflows/ci-cd.yml`.

### Flujo del Pipeline

```
Push a main / Pull Request
        |
        v
+-------------------+     +--------------------+
| Test Backend      |     | Test Frontend      |
| - Setup Python    |     | - Setup Node.js    |
| - Install deps    |     | - npm ci           |
| - Verify imports  |     | - npm run build    |
+-------------------+     +--------------------+
        |                          |
        +----------+---------------+
                   |
                   v  (solo push a main)
        +------------------------+
        | Build & Push Docker    |
        | - Build backend image  |
        | - Build frontend image |
        | - Push a GHCR          |
        +------------------------+
                   |
                   v
        +------------------------+
        | Deploy to Production   |
        | - SSH al servidor      |
        | - Pull imagenes        |
        | - docker-compose up    |
        | - Health check         |
        +------------------------+
```

### Jobs del Pipeline

| Job | Trigger | Descripcion |
|---|---|---|
| **test-backend** | Push y PR a `main` | Instala dependencias Python y verifica que la aplicacion arranca correctamente |
| **test-frontend** | Push y PR a `main` | Instala dependencias Node.js, ejecuta build de produccion y verifica el output |
| **build-docker** | Solo push a `main` | Construye imagenes Docker y las publica en GitHub Container Registry (GHCR) |
| **deploy** | Solo push a `main` | Despliega automaticamente al servidor de produccion via SSH |

### Secrets requeridos en GitHub

| Secret | Descripcion |
|---|---|
| `SSH_HOST` | IP o dominio del servidor de produccion |
| `SSH_USER` | Usuario SSH del servidor |
| `SSH_KEY` | Clave privada SSH para autenticacion |
| `GITHUB_TOKEN` | Se genera automaticamente por GitHub Actions |

### Configurar los secrets

1. Ir a **Settings** > **Secrets and variables** > **Actions** en el repositorio de GitHub
2. Crear los secrets `SSH_HOST`, `SSH_USER` y `SSH_KEY`
3. Asegurar que la clave publica correspondiente a `SSH_KEY` esta en `~/.ssh/authorized_keys` del servidor

---

## :shield: Seguridad

El sistema implementa multiples capas de seguridad:

### Autenticacion y Autorizacion

- **Autenticacion en dos factores (2FA)** obligatoria mediante codigo OTP enviado por correo electronico
- **Hashing de contrasenas** con bcrypt (factor de costo adaptativo)
- **Tokens JWT** para sesiones sin estado, con expiracion configurable
- **Revocacion de tokens** para cierre de sesion seguro
- **Control de acceso basado en roles (RBAC)** con 8 roles diferenciados

### Proteccion de la Aplicacion

- **Rate Limiting** configurado por zona en Nginx:
  - Endpoints generales: 10 req/s por IP
  - Endpoints de API: 20 req/s por IP
  - Endpoints de autenticacion: 3 req/s por IP (proteccion contra fuerza bruta)
  - Subida de archivos: 2 req/s por IP
- **Configuracion CORS** restrictiva con origenes permitidos explicitamente
- **Validacion de entrada** en todos los endpoints mediante esquemas Pydantic

### Headers de Seguridad

La configuracion de Nginx incluye los siguientes headers de seguridad:

| Header | Valor |
|---|---|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` |
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Content-Type-Options` | `nosniff` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Content-Security-Policy` | Politica restrictiva con `default-src 'self'` |

### Seguridad de la Infraestructura

- **HTTPS obligatorio** con redireccion automatica de HTTP a HTTPS
- **TLS 1.2 y TLS 1.3** exclusivamente (protocolos antiguos deshabilitados)
- **OCSP Stapling** habilitado para verificacion eficiente de certificados
- **Tokens del servidor ocultos** (`server_tokens off`)
- **Acceso denegado a archivos ocultos** (dotfiles)
- **Middleware UTF-8** para garantizar la codificacion correcta en todas las respuestas
- **Middleware de headers de seguridad** adicional en FastAPI
- **Logging estructurado** de todas las peticiones para auditoria

---

## :scroll: Licencia

Este proyecto esta licenciado bajo la **Licencia MIT**. Consultar el archivo [LICENSE](LICENSE) para mas detalles.

---

## :bust_in_silhouette: Autor

**Deivinsonn Morales**

---

<div align="center">

*Desarrollado con :heart: para la gestion integral de seguridad industrial y salud ocupacional*

**v2.0.0**

</div>
