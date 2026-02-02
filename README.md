# 🚀 Sistema de Gestión de Programas y Actividades

> Backend profesional para la gestión de programas, actividades y ejecuciones con control de permisos por roles.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Arquitectura](#-arquitectura)
- [Instalación Rápida](#-instalación-rápida)
- [Uso](#-uso)
- [Endpoints API](#-endpoints-api)
- [Modelo de Datos](#-modelo-de-datos)
- [Roles y Permisos](#-roles-y-permisos)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)

---

## ✨ Características

- ✅ **CRUD Completo** para Programas, Actividades y Ejecuciones
- 🔐 **Autenticación JWT** con tokens seguros
- 👥 **Control de Acceso** basado en roles (Administrador, Coordinador, Supervisor, Empleado)
- 📊 **Sistema de Reportes** con estadísticas y métricas
- 🐳 **Dockerizado** para despliegue portátil
- 📝 **Documentación Interactiva** con Swagger UI
- 💾 **Persistencia** con SQLite y SQLAlchemy ORM
- ✔️ **Validación de Datos** con Pydantic

---

## 🛠️ Tecnologías

| Categoría | Tecnología |
|-----------|-----------|
| **Framework** | FastAPI |
| **Lenguaje** | Python 3.11+ |
| **ORM** | SQLAlchemy |
| **Base de Datos** | SQLite |
| **Validación** | Pydantic |
| **Autenticación** | JWT (python-jose) |
| **Seguridad** | Bcrypt (passlib) |
| **Contenedores** | Docker |

---

## 🏗️ Arquitectura

### Estructura del Proyecto

```
gestion_proyectos/
│
├── app/
│   ├── main.py              # Punto de entrada de la aplicación
│   │
│   ├── core/                # Configuración global
│   │   ├── database.py      # Conexión a la base de datos
│   │   ├── security.py      # JWT y hashing de contraseñas
│   │   └── dependencies.py  # Dependencias compartidas
│   │
│   ├── models/              # Modelos SQLAlchemy (Tablas)
│   │   ├── user.py
│   │   ├── program.py
│   │   ├── activity.py
│   │   └── execution.py
│   │
│   ├── schemas/             # Esquemas Pydantic (Validación)
│   │   ├── user.py
│   │   ├── program.py
│   │   ├── activity.py
│   │   └── execution.py
│   │
│   └── routes/              # Endpoints de la API
│       ├── auth.py
│       ├── users.py
│       ├── programs.py
│       ├── activities.py
│       ├── executions.py
│       └── reports.py
│
├── Dockerfile               # Configuración de Docker
├── requirements.txt         # Dependencias de Python
└── README.md               # Este archivo
```

### Flujo de Datos

```
Cliente → Schema (Validación) → Route (Lógica) → Model (Base de Datos) → Response
```

---

## 🚀 Instalación Rápida

### Prerrequisitos

- Docker instalado ([Descargar Docker](https://www.docker.com/get-started))
- Puerto 8080 disponible

### Paso 1: Clonar el repositorio

```bash
git clone <tu-repositorio>
cd gestion_proyectos
```

### Paso 2: Construir la imagen Docker

```bash
docker build -t gestion-proyectos-app .
```

### Paso 3: Ejecutar el contenedor

```bash
docker run -d -p 8080:80 --name mi-proyecto-contenedor gestion-proyectos-app
```

### Paso 4: Verificar que está funcionando

```bash
docker logs mi-proyecto-contenedor
```

Deberías ver:
```
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:80
```

### 🎉 ¡Listo!

Accede a la documentación interactiva en: **http://localhost:8080/docs**

---

## 📖 Uso

### 1. Crear un Usuario

**Endpoint:** `POST /users/`

```json
{
  "email": "admin@ejemplo.com",
  "password": "contraseña_segura",
  "full_name": "Administrador Principal",
  "role": "Administrador"
}
```

### 2. Autenticarse

**Endpoint:** `POST /login`

- **username:** `admin@ejemplo.com`
- **password:** `contraseña_segura`

Recibirás un token JWT. **Cópialo.**

### 3. Autorizar en Swagger

1. Haz clic en el botón verde **"Authorize"** 🔓
2. Pega el token en el campo "Value"
3. Haz clic en **"Authorize"**
4. Cierra el modal

Ahora el candado debería estar **cerrado** 🔒

### 4. Usar la API

Con la sesión autorizada, puedes:

- Crear programas, actividades y ejecuciones
- Consultar reportes
- Actualizar y eliminar registros (según tu rol)

---

## 📡 Endpoints API

### 🔐 Autenticación

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| POST | `/users/` | Crear usuario | No |
| POST | `/login` | Iniciar sesión | No |

### 📋 Programas

| Método | Endpoint | Descripción | Roles Permitidos |
|--------|----------|-------------|------------------|
| POST | `/programs/` | Crear programa | Admin, Coordinador |
| GET | `/programs/` | Listar programas | Todos |
| GET | `/programs/{id}` | Obtener programa | Todos |
| PUT | `/programs/{id}` | Actualizar programa | Admin, Coordinador |
| DELETE | `/programs/{id}` | Eliminar programa | Admin |

### ⚡ Actividades

| Método | Endpoint | Descripción | Roles Permitidos |
|--------|----------|-------------|------------------|
| POST | `/activities/` | Crear actividad | Admin, Coordinador, Supervisor |
| GET | `/activities/` | Listar actividades | Todos |
| GET | `/activities/{id}` | Obtener actividad | Todos |
| GET | `/activities/program/{id}` | Actividades por programa | Todos |
| PUT | `/activities/{id}` | Actualizar actividad | Admin, Coordinador, Supervisor |
| DELETE | `/activities/{id}` | Eliminar actividad | Admin |

### ✅ Ejecuciones

| Método | Endpoint | Descripción | Roles Permitidos |
|--------|----------|-------------|------------------|
| POST | `/executions/` | Registrar ejecución | Todos |
| GET | `/executions/` | Listar ejecuciones | Todos* |
| GET | `/executions/{id}` | Obtener ejecución | Propietario, Admin, Supervisor |
| GET | `/executions/my-executions` | Mis ejecuciones | Todos |
| GET | `/executions/activity/{id}` | Ejecuciones por actividad | Todos |
| PUT | `/executions/{id}` | Actualizar ejecución | Propietario, Admin, Supervisor |
| DELETE | `/executions/{id}` | Eliminar ejecución | Admin |

*Admin y Supervisor ven todas; otros usuarios solo ven las propias.

### 📊 Reportes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/reports/` | Info del módulo |
| GET | `/reports/general` | Dashboard general |
| GET | `/reports/programs` | Resumen de programas |
| GET | `/reports/program/{id}` | Detalle de programa |
| GET | `/reports/user/{id}` | Rendimiento de usuario |
| GET | `/reports/activity/{id}` | Estadísticas de actividad |

---

## 🗄️ Modelo de Datos

### Diagrama de Relaciones

```
┌─────────────┐
│    User     │
│─────────────│
│ id (PK)     │
│ email       │
│ password    │
│ full_name   │
│ role        │
└──────┬──────┘
       │
       │ coordinator_id
       │
┌──────▼──────┐
│   Program   │
│─────────────│
│ id (PK)     │
│ name        │
│ description │
└──────┬──────┘
       │
       │ program_id
       │
┌──────▼──────┐
│  Activity   │
│─────────────│
│ id (PK)     │
│ name        │
│ description │
└──────┬──────┘
       │
       │ activity_id + user_id
       │
┌──────▼──────────┐
│   Execution     │
│─────────────────│
│ id (PK)         │
│ observation     │
│ status          │
│ execution_date  │
└─────────────────┘
```

### Estados de Ejecución

- **Completado:** Tarea finalizada exitosamente
- **Pendiente:** Tarea en progreso
- **Con Novedad:** Tarea con incidencias

---

## 👥 Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **Administrador** | Control total del sistema |
| **Coordinador** | Crear/editar programas y actividades |
| **Supervisor** | Crear actividades, ver todo |
| **Empleado** | Registrar ejecuciones, ver asignado |

---

## 🛠️ Troubleshooting

### Error: "Container name is already in use"

```bash
docker rm -f mi-proyecto-contenedor
docker run -d -p 8080:80 --name mi-proyecto-contenedor gestion-proyectos-app
```

### Error: 401 Unauthorized

- ✅ Verifica que hiciste login
- ✅ Verifica que el token no expiró (30 minutos)
- ✅ Verifica que el candado esté cerrado 🔒

### Error: 500 Internal Server Error

```bash
docker logs mi-proyecto-contenedor
```

Busca el `Traceback` y comparte el error.

### Cambié el código pero no se actualiza

```bash
docker stop mi-proyecto-contenedor
docker rm mi-proyecto-contenedor
docker build -t gestion-proyectos-app .
docker run -d -p 8080:80 --name mi-proyecto-contenedor gestion-proyectos-app
```

### Base de datos se borra al reiniciar

Usa volúmenes para persistencia:

```bash
docker run -d -p 8080:80 -v ${PWD}:/code --name mi-proyecto-contenedor gestion-proyectos-app
```

---

## 📚 Comandos Docker Útiles

```bash
# Ver contenedores corriendo
docker ps

# Ver logs
docker logs mi-proyecto-contenedor

# Ver logs en tiempo real
docker logs -f mi-proyecto-contenedor

# Entrar al contenedor
docker exec -it mi-proyecto-contenedor bash

# Detener contenedor
docker stop mi-proyecto-contenedor

# Reiniciar contenedor
docker restart mi-proyecto-contenedor

# Ver espacio usado
docker system df

# Limpiar todo (cuidado)
docker system prune -a
```

---

## 🗺️ Roadmap

### Versión 1.1 (Próximo)
- [ ] Filtros avanzados por fecha y estado
- [ ] Paginación de resultados
- [ ] Validaciones de negocio (evitar duplicados)

### Versión 1.2
- [ ] Migración a PostgreSQL
- [ ] Variables de entorno con `.env`
- [ ] Tests automatizados con Pytest

### Versión 2.0
- [ ] Frontend con React
- [ ] Gráficos con Chart.js
- [ ] Despliegue en la nube

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

## 👨‍💻 Autor

**Tu Nombre**  
📧 Email: dmobri24010211@gmail.com
🔗 LinkedIn: linkedin.com/in/deivinsonn-morales-brito-298352208 
🐙 GitHub: Dmobri87 (https://github.com)

---

## 🙏 Agradecimientos

Construido con ❤️ usando FastAPI y Python.

---

**¿Preguntas?** Abre un issue en el repositorio o contacta al equipo de desarrollo.