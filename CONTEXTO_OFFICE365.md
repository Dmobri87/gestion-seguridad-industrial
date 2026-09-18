# Contexto Completo — Migración Gestión GAE → Office 365
**Fecha de exploración:** 2026-03-07
**App origen:** http://localhost (Docker — FastAPI + React 18 + PostgreSQL)
**App destino:** SharePoint Online (`ssidesarrollo.sharepoint.com/sites/SeguridadIndustrial`)

---

## 🗂️ MÓDULOS DEL SISTEMA (10 módulos)

---

### 1. 📊 DASHBOARD — Panel de Gestión GAE
**Ruta:** `/dashboard`

**KPIs principales (4 tarjetas de color):**
- 🟢 **Accidentes del Mes** — contador + badge "Objetivo cumplido" / "Sin accidentes"
- 🔴 **Emergencias Atendidas** — contador + tiempo promedio respuesta (min)
- 🟠 **Cumplimiento General %** — porcentaje acumulado del año
- 🟣 **Actividades Pendientes** — contador "Por ejecutar este mes"

**Filtros:** Selector de Mes + Año + botón "Recalcular"

**Sección inferior izquierda:**
- Gráfico de línea: **Tendencia de Cumplimiento** (últimos 6 meses, escala 0-100%)

**Sección inferior derecha:**
- Lista: **Cumplimiento por Categoría** (con barra de progreso y %)
  - PRIMEROS AUXILIOS, ENTRENAMIENTO, PROCESOS, INTEGRIDAD OPERACIONAL, ASEGURAMIENTO, SALUD Y SEGURIDAD, SOPORTE A PRODUCCION, PDI

**Sección adicional (más abajo):**
- 🏆 **Top Performers** — ranking de TAEs (sin datos = "Sin datos")
- 🔧 **Equipos Operativos** — X/7 con desglose: En Mtto / Fuera Serv. / Pend. Mtto
- 🛡️ **Certificaciones** — total + desglose: Vencidas / <7 días / <30 días

---

### 2. 📋 CATÁLOGO — Catálogo de Actividades
**Ruta:** `/catalogo`

**Dos pestañas:**

#### Pestaña 1: Plantillas de Actividades (53 plantillas)
- Agrupadas por categoría (colapsables)
- Cada plantilla tiene: Código (ej. PRIMEROS_AUXILIOS-001), Nombre, Descripción
- Acciones: ✏️ Editar, 🗑️ Eliminar
- Botón: **+ Nueva Plantilla**

#### Pestaña 2: Categorías (10 categorías)
Columnas: Color (cuadrado), Código, Nombre, Descripción, Actividades (contador), Estado, Acciones

| Código | Nombre | Actividades |
|--------|--------|-------------|
| PLAN_DE_DESARROLLO | PDI | 2 |
| OPERACIONAL | OPERACIONAL | 9 |
| PRIMEROS_AUXILIOS | PRIMEROS AUXILIOS | 4 |
| INTEGRIDAD_OPERACIONAL | INTEGRIDAD OPERACIONAL | (visible arriba) |
| ENTRENAMIENTO | ENTRENAMIENTO | 11 |
| ASEGURAMIENTO | ASEGURAMIENTO | 9 |
| SALUD_Y_SEGURIDAD | SALUD Y SEGURIDAD | 2 |
| PROCESOS | PROCESOS | 2 |
| SOPORTE_A_PRODUCCION | SOPORTE A PRODUCCION | 5 |

- Botón: **+ Nueva Categoría**

---

### 3. 📅 PLANIFICACIÓN — Planes Mensuales
**Ruta:** `/planificacion`

**Tabla de planes:**
- Columnas: Personal, Período, Estado, Planeado, Ejecutado, Cumplimiento, Acciones
- Filtros: Mes + Año
- Botón: **+ Programar Planes**
- Botón secundario: **Auditoría**
- Sin datos en Marzo 2026 (base de datos vacía)

**Flujo:** Admin programa actividades por TAE para el mes → TAE las ejecuta → Se mide cumplimiento

---

### 4. ⚡ EJECUCIÓN — Registro de Ejecuciones
**Ruta:** `/ejecucion`

**KPIs (6 contadores):**
- Total Ejecutadas ✅
- Completadas ✓
- Con Novedad ⚠️
- Por Aprobar 🕐
- Aprobadas ✅
- Rechazadas ✗

**Filtros:** Filtrar por TAE + Mes + Año
**Botón:** **+ Nueva Ejecución**

**4 pestañas de vista:**
1. **Mis Pendientes** 🔥 — actividades pendientes del TAE logueado
2. **Historial** 📅 — historial completo
3. **Por Aprobar** 🕐 — esperando aprobación del supervisor
4. **Rechazadas** ✗ — ejecuciones rechazadas

**Flujo de aprobación:** TAE registra ejecución → Supervisor aprueba/rechaza → Se registra en historial

---

### 5. 🚨 EMERGENCIAS — Registro de Emergencias
**Ruta:** `/emergencias`

**KPIs (4 tarjetas):**
- Total Emergencias 🔔
- Activas
- Tiempo Resp. Promedio (min)
- Cerradas

**Tabla:**
- Columnas: Fecha/Hora, Tipo, Ubicación, Prioridad, Estado, Tiempo Resp., Acciones
- Filtros: Mes + Año
- Botón: **+ Reportar Emergencia** (rojo)

**Formulario "Reportar Emergencia":**
- Tipo de Emergencia (dropdown — catálogo SSI_TiposEmergencia)
- Ubicación (texto — ej. "Ej: Nivel +50, Galería Norte")
- Prioridad (dropdown)
- Descripción (textarea)
- Botones: Cancelar / Reportar

---

### 6. 🔧 EQUIPOS — Inventario de Equipos (EPP)
**Ruta:** `/equipos`

**KPIs (4 tarjetas):**
- Total Equipos: 7
- Operativos: 7/7
- Disp. Turno Día: 7/7 ☀️
- Disp. Turno Noche: 7/7 🌙

**3 pestañas + vista especial:**
1. **Todos (7)**
2. **Operativos (7)**
3. **Fuera de Servicio (0)**
4. **🔄 Flota por Turnos**

**Tabla columnas:** N°, Código, Nombre, Categoría, Ubicación, Estado, Disponibilidad (Día/Noche), Próx. Mantto., Acciones

**Datos reales (7 equipos):**
| Código | Nombre | Categoría | Ubicación | Próx. Mantto |
|--------|--------|-----------|-----------|--------------|
| AMB-001 | Ambulancia TAE-01 | Ambulancias | Base Principal | 03/05/2026 |
| AMB-002 | Ambulancia TAE-02 | Ambulancias | Base Norte | 18/04/2026 |
| RESC-001 | Camioneta Rescate | Vehículos de Rescate | Base Principal | 18/05/2026 |
| SCBA-001 | SCBA Drager PSS-7000 | SCBA | Ambulancia TAE-01 | 17/02/2027 |
| SCBA-002 | SCBA Drager PSS-7000 | SCBA | Ambulancia TAE-02 | 17/02/2027 |
| EXT-001 | Extintor PQS 20lb | Extintores | Ambulancia TAE-01 | 16/08/2026 |
| RAD-001 | Radio Motorola DGP8550 | Comunicaciones | Ambulancia TAE-01 | 17/02/2027 |

- Botón: **+ Agregar Equipo**
- Vista detalle por equipo: botón **Ver**

---

### 7. 🎓 CERTIFICACIONES — Gestión de Certificaciones
**Ruta:** `/certificaciones`

**3 pestañas:**
1. **Por Vencer (0)** ⚠️ — semáforo de días restantes
2. **Por TAE** 👤 — dropdown "Selecciona un TAE" → muestra certificaciones del TAE
3. **Tipos** 🛡️ — catálogo de tipos de certificación

**Botón:** **+ Registrar Certificación**

**Flujo:** Registro de certificación por TAE con fecha de vencimiento → Alerta automática cuando se acerca el vencimiento

---

### 8. 📈 REPORTES — Reportes y Exportación
**Ruta:** `/reportes`

**Descripción:** "Genera reportes en Excel o PDF para cumplimiento, emergencias, equipos, certificaciones y resumen ejecutivo."

**Controles:**
- Tipo de reporte (dropdown): Cumplimiento Mensual, (otros tipos)
- Formato: Excel / PDF
- Año: 2026
- Mes: Marzo
- Usuario (opcional): ID usuario

**Acciones:** Vista previa + Descargar + Excel (acceso rápido)

**Tipos de reportes disponibles:**
- Cumplimiento Mensual
- Emergencias
- Equipos
- Certificaciones
- Resumen Ejecutivo

---

### 9. 🏅 DESEMPEÑO TAEs
**Ruta:** `/desempeno`

**KPIs (4 tarjetas):**
- Total TAEs: 4
- Cumplimiento Promedio: 0.0%
- Cumplimiento > 80%: 0/4 ✅
- Cumplimiento < 50%: 4 🕐

**3 pestañas:**
1. **Ranking** 🏆 — tabla comparativa de todos los TAEs
2. **Alertas (4)** 🕐 — TAEs con bajo cumplimiento
3. **Top Performers** 🏆 — mejores del período

**Tabla Ranking:**
- Columnas: #, Plan/TAE, Departamento, Plan (ej. 0/0), Cumplimiento (barra), Aprobadas, Pendientes, Rechazadas
- Datos: Armando Plata, Carlos Fonseca, Yohana Barrantes, Guillermo Castañeda (todos en grupo Jaguares)
- Botón: **Exportar**

---

### 10. ⚙️ ADMINISTRACIÓN
**Ruta:** `/administracion`

**2 pestañas:**

#### Usuarios (8 usuarios)
Columnas: Usuario (nombre + email), Rol, Grupo, Estado, Acciones

| Nombre | Rol | Grupo | Email |
|--------|-----|-------|-------|
| Armando Plata | TAE | Jaguares | armando.plata@cerrejon.com |
| Carlos Fonseca | TAE | Jaguares | carlos.fonseca@cerrejon.com |
| Yohana Barrantes | TAE | Jaguares | yohana.barrantes@cerrejon.com |
| Guillermo Castañeda | TAE | Jaguares | guillermo.castaneda@cerrejon.com |
| Aurelio Soto | PSE | Jaguares | aurelio.soto@cerrejon.com |
| Marco Maestre | PSE | Jaguares | marco.maestre@cerrejon.com |
| Oscar Ospino | PSE | Jaguares | oscar.ospino@cerrejon.com |
| Administrador | Administrador | Sin grupo | admin@cerrejon.com |

- Filtros: Filtrar por rol / Filtrar por grupo
- Botón: **+ Nuevo Usuario**

#### Grupos de Trabajo (6 grupos)
Tarjetas con: Nombre, "Sin coordinador", descripción, 0 miembros

| Grupo |
|-------|
| Cardenales |
| Corsarios |
| Guerreros |
| Jaguares |
| Valientes |
| Vikingos |

- Botón: **+ Nuevo Grupo**

---

## 🔄 MAPEO SHAREPOINT — Listas necesarias

| Módulo GAE | Lista SharePoint | Estado |
|------------|-----------------|--------|
| Emergencias | SSI_Emergencias | ✅ Creada |
| Equipos/EPP | SSI_Equipos | ✅ Creada |
| Certificaciones | SSI_Certificaciones | ✅ Creada |
| Accidentes | SSI_Accidentes | ✅ Creada |
| Usuarios/TAEs | SSI_Usuarios | ✅ Creada |
| Tipos Emergencia | SSI_TiposEmergencia | ✅ Creada |
| Tipos Certificación | SSI_TiposCertificacion | ✅ Creada |
| Grupos de Trabajo | SSI_GruposTrabajo | ✅ Creada |
| Ejecuciones | SSI_Ejecuciones | ✅ Creada |
| Inspecciones | SSI_Inspecciones | ✅ Creada |
| Mantenimientos | SSI_Mantenimientos | ✅ Creada |
| Catálogo/Plantillas | (pendiente confirmar) | ❓ |
| Planificación | (pendiente confirmar) | ❓ |

---

## 🚧 Estado de la app SharePoint (app-v2.js)

**Problema actual:** El script `app-v2.js` no se inyecta automáticamente al cargar la página.

**Causa:** No hay mecanismo persistente de carga (UserCustomAction sin configurar).

**Solución prioritaria:** Implementar `UserCustomAction ScriptBlock` vía SharePoint REST API para que el JS se cargue automáticamente en cada visita a la página.

**Bug conocido en app-v2.js:** Error de backtick en template literals — necesita corrección antes de despliegue.

---

## 📋 PRIORIDAD DE IMPLEMENTACIÓN en Office 365

Según complejidad y valor de negocio:

1. **Dashboard** — KPIs desde listas SP (READ-only, sin CRUD)
2. **Emergencias** — CRUD completo, formulario modal (YA parcialmente hecho)
3. **Equipos** — inventario EPP con datos reales (7 equipos cargados)
4. **Certificaciones** — semáforo de vencimiento por TAE
5. **Desempeño TAEs** — ranking y alertas (requiere Ejecuciones)
6. **Catálogo** — 53 plantillas + 10 categorías
7. **Planificación** — planes mensuales por TAE
8. **Ejecución** — flujo de aprobación TAE → Supervisor
9. **Reportes** — Excel/PDF (Power Automate o JS)
10. **Administración** — usuarios y grupos (solo lectura en SP)
