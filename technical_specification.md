# 📋 ESPECIFICACIÓN TÉCNICA COMPLETA
## Sistema Enterprise de Gestión de Seguridad Industrial y Salud Ocupacional

**Versión:** 2.0  
**Fecha:** Enero 2026  
**Autor:** Equipo de Desarrollo  
**Cliente:** Empresa Minera/Industrial  

---

## 📑 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Alcance del Proyecto](#alcance-del-proyecto)
3. [Requisitos Funcionales](#requisitos-funcionales)
4. [Requisitos No Funcionales](#requisitos-no-funcionales)
5. [Arquitectura del Sistema](#arquitectura-del-sistema)
6. [Modelo de Datos](#modelo-de-datos)
7. [Casos de Uso](#casos-de-uso)
8. [Interfaces de Usuario](#interfaces-de-usuario)
9. [Seguridad](#seguridad)
10. [Plan de Implementación](#plan-de-implementación)
11. [Roadmap y Estimaciones](#roadmap-y-estimaciones)

---

## 1. RESUMEN EJECUTIVO

### 1.1 Propósito del Sistema

El sistema gestiona integralmente las actividades de seguridad industrial, salud ocupacional y atención de emergencias en empresas del sector minero/industrial.

### 1.2 Objetivos Principales

- ✅ Reducir accidentes laborales a CERO
- ✅ Automatizar planificación y seguimiento de actividades de seguridad
- ✅ Calcular cumplimiento automático (Planeado vs Ejecutado)
- ✅ Gestionar inventario de equipos de seguridad
- ✅ Controlar certificaciones y vencimientos
- ✅ Registrar y dar seguimiento a emergencias
- ✅ Generar reportes de cumplimiento regulatorio

### 1.3 Usuarios del Sistema

| Rol | Cantidad | Permisos |
|-----|----------|----------|
| **Administrador** | 1-2 | Control total |
| **Coordinador de Seguridad** | 2-5 | Planificación, reportes |
| **Supervisor** | 5-10 | Aprobaciones, seguimiento |
| **TAE (Técnico en Emergencias)** | 10-30 | Ejecución, registro |
| **Empleado General** | 50-100 | Consulta, reportes personales |
| **Invitado/Auditor** | Variable | Solo lectura |

**Total usuarios esperados:** 10-150 por organización

### 1.4 Módulos del Sistema

```
┌─────────────────────────────────────────────────────┐
│                  SISTEMA CENTRAL                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. PLANIFICACIÓN                                   │
│     └─ Plan mensual por usuario                     │
│     └─ Ciclos de planificación (1-3)                │
│     └─ Metas por actividad                          │
│                                                      │
│  2. EJECUCIÓN                                        │
│     └─ Registro de actividades                      │
│     └─ Evidencias (fotos, PDFs)                     │
│     └─ Aprobaciones                                 │
│                                                      │
│  3. EMERGENCIAS                                      │
│     └─ Registro de eventos                          │
│     └─ Tiempos de respuesta                         │
│     └─ Recursos utilizados                          │
│                                                      │
│  4. EQUIPOS E INVENTARIO                            │
│     └─ Ambulancias, SCBA, Radios                    │
│     └─ Mantenimientos                               │
│     └─ Inspecciones                                 │
│                                                      │
│  5. CERTIFICACIONES                                  │
│     └─ Personal (altura, conducción)                │
│     └─ Vehículos (SOAT, revisión)                   │
│     └─ Alertas de vencimiento                       │
│                                                      │
│  6. CUMPLIMIENTO Y REPORTES                         │
│     └─ Dashboard ejecutivo                          │
│     └─ KPIs de seguridad                            │
│     └─ Exportación Excel/PDF                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 2. ALCANCE DEL PROYECTO

### 2.1 Incluido en el Sistema

#### Módulo 1: Planificación
- Crear plan mensual por usuario
- Dividir mes en 3 ciclos de planificación
- Definir cantidad de veces que se ejecuta cada actividad
- Asignar actividades por categoría
- Plantillas de actividades predefinidas (53 actividades)

#### Módulo 2: Ejecución
- Registrar ejecución diaria
- Adjuntar evidencias (fotos, PDFs, videos)
- Sistema de aprobación por supervisor
- Edición con autorización
- Historial de cambios (auditoría)

#### Módulo 3: Emergencias
- 8 tipos de emergencias predefinidas
- Registro de eventos
- Tiempos de respuesta
- Recursos utilizados
- Seguimiento de cierre

#### Módulo 4: Equipos
- Inventario completo
- Categorías: Ambulancias, SCBA, Radios, Bombas CI, etc.
- Mantenimientos preventivos/correctivos
- Inspecciones
- Alertas de próximo mantenimiento

#### Módulo 5: Certificaciones
- Personal: Altura, Conducción, Primeros Auxilios
- Vehículos: SOAT, Revisión Técnico-Mecánica
- Alertas 30/15/7 días antes de vencimiento
- Email/Notificación automática

#### Módulo 6: Reportes
- Dashboard ejecutivo
- Cumplimiento mensual/anual
- Por usuario, categoría, departamento
- Exportar Excel/PDF
- Gráficos de tendencias

### 2.2 Excluido del Alcance (Futuras Fases)

- ❌ Integración con nómina
- ❌ Módulo de costos y presupuesto
- ❌ App móvil nativa (solo PWA)
- ❌ Inteligencia artificial predictiva
- ❌ Geolocalización en tiempo real

---

## 3. REQUISITOS FUNCIONALES

### RF-001: Planificación Mensual

**Actor:** Coordinador de Seguridad  
**Descripción:** Crear plan mensual para un TAE

**Flujo Principal:**
1. Coordinador selecciona usuario (TAE)
2. Selecciona mes/año
3. Sistema muestra plantilla de 53 actividades agrupadas por 10 categorías
4. Coordinador define cantidad de veces por actividad por ciclo
5. Sistema calcula total mensual
6. Coordinador aprueba plan
7. Sistema notifica al TAE

**Reglas de Negocio:**
- RN-001: Un usuario solo puede tener UN plan por mes
- RN-002: Las cantidades deben ser números enteros positivos
- RN-003: El plan puede editarse solo si el mes no ha iniciado

### RF-002: Registro de Ejecución

**Actor:** TAE  
**Descripción:** Registrar ejecución de actividad planeada

**Flujo Principal:**
1. TAE ve lista de actividades planeadas para hoy
2. Selecciona actividad
3. Completa observaciones
4. Adjunta evidencias (obligatorias por defecto)
5. Selecciona estado: Completado/Pendiente/Con Novedad
6. Sistema registra con timestamp
7. Sistema actualiza contador de cumplimiento

**Reglas de Negocio:**
- RN-004: Solo se puede ejecutar actividad que esté en el plan
- RN-005: Una ejecución puede editarse dentro de 24 horas
- RN-006: Ediciones posteriores requieren aprobación de Coordinador
- RN-007: Las evidencias son obligatorias por defecto en toda actividad planificada
- RN-008: Coordinador y Administrador pueden exceptuar manualmente el requisito por actividad

### RF-003: Cálculo de Cumplimiento

**Actor:** Sistema  
**Descripción:** Calcular automáticamente % de cumplimiento

**Fórmula:**
```
Cumplimiento (%) = (Total Ejecutado / Total Planeado) × 100
```

**Niveles:**
- **Por Actividad:** Individual
- **Por Categoría:** Suma de todas las actividades de la categoría
- **Por Mes:** Suma de todas las categorías
- **Por Año:** Promedio de 12 meses

**Reglas de Negocio:**
- RN-009: Se calcula en tiempo real
- RN-010: Se redondea a 2 decimales
- RN-011: Se guarda snapshot al final del mes

### RF-004: Gestión de Emergencias

**Actor:** TAE, Coordinador  
**Descripción:** Registrar y gestionar emergencias

**Tipos de Emergencias:**
1. Lesión AL
2. Conato de incendio
3. Daños a propiedad
4. Enfermedad general
5. Impacto ambiental
6. Atención a comunidad
7. Incidente deportivo
8. No clasificado

**Flujo Principal:**
1. TAE recibe alerta de emergencia
2. Registra tipo, ubicación, hora
3. Marca hora de llegada (calcula tiempo de respuesta)
4. Describe acciones tomadas
5. Adjunta evidencias
6. Define severidad
7. Cierra evento o escala a Coordinador

**Métricas:**
- Tiempo de respuesta (minutos)
- Recursos utilizados
- Personal involucrado
- Costo estimado

### RF-005: Inventario de Equipos

**Actor:** Coordinador, Supervisor  
**Descripción:** Gestionar inventario de equipos de seguridad

**Categorías de Equipos:**
1. Ambulancias
2. SCBA (Self-Contained Breathing Apparatus)
3. Radios de comunicación
4. Bombas contra incendio
5. Tanqueros
6. Arneses
7. Escaleras
8. Mangueras
9. Equipos menores

**Atributos por Equipo:**
- Código único
- Categoría
- Marca/Modelo
- Número de serie
- Fecha de compra
- Estado (Operativo/En Mantenimiento/Fuera de Servicio)
- Ubicación (CAE asignado)
- Próximo mantenimiento

### RF-006: Certificaciones y Vencimientos

**Actor:** Coordinador, Sistema  
**Descripción:** Controlar certificaciones de personal y vehículos

**Certificaciones de Personal:**
- Trabajo en altura
- Conducción de ambulancia
- Primeros auxilios
- Pase gris
- Manejo de SCBA
- Rescate en espacios confinados

**Documentos de Vehículos:**
- SOAT
- Revisión técnico-mecánica
- Licencia de conducción del conductor asignado

**Alertas:**
- 30 días antes: Notificación informativa
- 15 días antes: Alerta amarilla
- 7 días antes: Alerta roja
- Vencido: Bloqueo (no se puede asignar tareas)

---

## 4. REQUISITOS NO FUNCIONALES

### RNF-001: Rendimiento

- Tiempo de respuesta: < 2 segundos para 95% de operaciones
- Carga de dashboard: < 3 segundos
- Generación de reportes: < 10 segundos
- Soporte para 100 usuarios concurrentes

### RNF-002: Disponibilidad

- Uptime: 99.5% (máximo 3.6 horas de downtime al mes)
- Backup automático diario
- Recuperación ante desastres: < 4 horas

### RNF-003: Seguridad

- Autenticación: JWT con expiración 30 minutos
- Contraseñas: Bcrypt con salt
- HTTPS obligatorio en producción
- 2FA para administradores
- Logs de auditoría completos
- Encriptación de datos sensibles en reposo

### RNF-004: Usabilidad

- Interfaz intuitiva (usuario promedio aprende en < 30 min)
- Responsive design (móvil, tablet, desktop)
- Soporte para navegadores modernos (últimas 2 versiones)
- Accesibilidad: WCAG 2.1 nivel AA

### RNF-005: Escalabilidad

- Arquitectura multi-tenant
- Soportar hasta 50 organizaciones
- Base de datos: hasta 10 millones de registros
- Almacenamiento de archivos: hasta 1TB

### RNF-006: Mantenibilidad

- Código modular y documentado
- Tests automatizados: coverage > 80%
- CI/CD implementado
- Documentación técnica completa

---

## 5. ARQUITECTURA DEL SISTEMA

### 5.1 Vista General

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTES                              │
│  [Web Browser]  [Mobile PWA]  [Tablet]                  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────┐
│               FRONTEND (React)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Dashboard │  │Ejecución │  │ Reportes │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────┐
│            BACKEND (FastAPI)                             │
│  ┌─────────────────────────────────────────┐            │
│  │    API Gateway & Authentication         │            │
│  └─────────────────────────────────────────┘            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Planificación│ │Ejecución│  │Emergencias│            │
│  └──────────┘  └──────────┘  └──────────┘             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Equipos │  │Certific. │  │ Reportes │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               CAPA DE DATOS                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐     │
│  │ PostgreSQL   │  │    Redis     │  │  MinIO   │     │
│  │ (Datos)      │  │   (Cache)    │  │(Archivos)│     │
│  └──────────────┘  └──────────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Stack Tecnológico

#### Frontend
- **Framework:** React 18+ con TypeScript
- **UI Library:** Ant Design / Material-UI
- **Estado:** Redux Toolkit
- **Gráficos:** Chart.js / Recharts
- **PWA:** Workbox

#### Backend
- **Framework:** FastAPI 0.100+
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Validación:** Pydantic V2
- **Auth:** JWT (python-jose)
- **Password:** Bcrypt (passlib)

#### Base de Datos
- **Principal:** PostgreSQL 15+
- **Cache:** Redis 7+
- **Archivos:** MinIO (S3-compatible)

#### DevOps
- **Containers:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana
- **Logs:** ELK Stack

### 5.3 Patrones de Diseño

- **Repository Pattern:** Abstracción de acceso a datos
- **Service Layer:** Lógica de negocio separada
- **DTO Pattern:** Pydantic schemas
- **Factory Pattern:** Creación de objetos complejos
- **Observer Pattern:** Sistema de notificaciones

---

## 6. MODELO DE DATOS

### 6.1 Diagrama Entidad-Relación (Simplificado)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│Organization │───────│ Department  │───────│    User     │
└─────────────┘       └─────────────┘       └──────┬──────┘
                                                    │
                                                    │
┌─────────────┐       ┌─────────────┐       ┌─────▼──────┐
│ActivityCat. │───────│ ActivityTpl │       │MonthlyPlan │
└─────────────┘       └──────┬──────┘       └──────┬─────┘
                             │                     │
                             │                     │
                      ┌──────▼──────┐       ┌──────▼─────┐
                      │PlannedActiv.│───────│PlanningCycl│
                      └──────┬──────┘       └────────────┘
                             │
                             │
                      ┌──────▼──────┐       ┌─────────────┐
                      │ExecutionActiv│──────│ExecutionFile│
                      └─────────────┘       └─────────────┘
```

### 6.2 Tablas Principales (35 tablas total)

#### Core (5 tablas)
1. `organizations` - Clientes multi-tenant
2. `departments` - Departamentos
3. `users` - Usuarios del sistema
4. `user_profiles` - Perfiles extendidos
5. `audit_logs` - Auditoría completa

#### Planificación (6 tablas)
6. `activity_categories` - 10 categorías
7. `activity_templates` - 53 actividades predefinidas
8. `monthly_plans` - Planes mensuales
9. `planning_cycles` - Ciclos de planificación
10. `planned_activities` - Actividades planeadas
11. `activity_goals` - Metas anuales

#### Ejecución (4 tablas)
12. `activity_executions` - Ejecuciones reales
13. `execution_files` - Evidencias adjuntas
14. `execution_approvals` - Aprobaciones
15. `execution_history` - Historial de cambios

#### Emergencias (3 tablas)
16. `emergency_types` - Tipos predefinidos
17. `emergencies` - Eventos de emergencia
18. `emergency_resources` - Recursos utilizados

#### Equipos (5 tablas)
19. `equipment_categories` - Categorías
20. `equipment` - Inventario
21. `equipment_maintenance` - Mantenimientos
22. `equipment_inspections` - Inspecciones
23. `equipment_files` - Documentos

#### Certificaciones (4 tablas)
24. `certification_types` - Tipos
25. `user_certifications` - Certificaciones personal
26. `vehicle_documents` - Documentos vehículos
27. `certification_alerts` - Alertas vencimiento

#### Cumplimiento (3 tablas)
28. `compliance_metrics` - Métricas calculadas
29. `monthly_summaries` - Resúmenes mensuales
30. `annual_summaries` - Resúmenes anuales

#### Notificaciones (2 tablas)
31. `notifications` - In-app notifications
32. `notification_settings` - Preferencias usuario

#### Accidentes (1 tabla)
33. `accidents` - KPI principal

#### Reportes (2 tablas)
34. `saved_reports` - Reportes guardados
35. `scheduled_reports` - Reportes automáticos

---

## 7. CASOS DE USO

### CU-001: Crear Plan Mensual

**Actor:** Coordinador de Seguridad  
**Precondición:** Usuario TAE existe en el sistema  

**Flujo Principal:**
1. Coordinador accede a "Planificación"
2. Selecciona TAE del dropdown
3. Selecciona mes/año
4. Sistema verifica que no exista plan para ese período
5. Sistema carga plantilla de 53 actividades
6. Coordinador ve tabla con 10 categorías
7. Para cada actividad, define cantidad por ciclo (1-3)
8. Sistema calcula totales
9. Coordinador revisa resumen
10. Click en "Crear Plan"
11. Sistema valida y guarda
12. Sistema envía notificación al TAE

**Flujo Alternativo 4a:** Plan ya existe
- Sistema muestra error
- Ofrece editar plan existente

### CU-002: Registrar Ejecución Diaria

**Actor:** TAE  
**Precondición:** Plan mensual aprobado

**Flujo Principal:**
1. TAE inicia sesión
2. Sistema muestra actividades del día
3. TAE selecciona actividad
4. Completa formulario:
   - Observaciones (texto)
   - Estado (dropdown)
   - Evidencias (upload archivos)
5. Click "Registrar"
6. Sistema valida
7. Sistema guarda con timestamp
8. Sistema actualiza cumplimiento
9. Sistema muestra confirmación

**Regla:** Solo actividades en plan actual

### CU-003: Ver Dashboard de Cumplimiento

**Actor:** Coordinador, Supervisor

**Flujo Principal:**
1. Usuario accede a Dashboard
2. Sistema carga:
   - KPI: Accidentes del mes (número)
   - Gráfico: Cumplimiento por categoría (barras)
   - Tabla: Top 5 TAEs con mayor cumplimiento
   - Lista: Actividades pendientes
   - Alertas: Vencimientos próximos
3. Usuario filtra por departamento/mes
4. Sistema actualiza visualización

---

## 8. INTERFACES DE USUARIO

### 8.1 Dashboard Ejecutivo

```
┌──────────────────────────────────────────────────────────┐
│  📊 DASHBOARD DE SEGURIDAD                 👤 Admin ▼   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  📅 Enero 2026                            🔄 Actualizar  │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  🚨 KPIs CRÍTICOS                                │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Accidentes    Emergencias    Cumplimiento      │    │
│  │      0             12            87%            │    │
│  │   ✅ Meta      📈 +3 vs mes     🟢 Bueno       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  📊 CUMPLIMIENTO POR CATEGORÍA                   │    │
│  │  ┌────────────────────────────────────────┐     │    │
│  │  │ ████████████████░░ SIO         81%     │     │    │
│  │  │ ██████████░░░░░░░░ Emergencias 53%     │     │    │
│  │  │ ████████████████████ Primeros A. 100%  │     │    │
│  │  │ ██████████████░░░░░░ Entrenam. 67%     │     │    │
│  │  └────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────┐  ┌──────────────────────┐     │
│  │ ⚠️ ALERTAS (5)       │  │ 📋 PENDIENTES (12)   │     │
│  ├─────────────────────┤  ├──────────────────────┤     │
│  │ • SOAT AMB-01       │  │ • Inspección SCBA    │     │
│  │   Vence en 7 días   │  │ • Medición caudales  │     │
│  │ • Certif. Altura    │  │ • Actualizar bitácora│     │
│  │   Juan P. 15 días   │  │ ...                  │     │
│  └─────────────────────┘  └──────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Pantalla de Planificación

```
┌──────────────────────────────────────────────────────────┐
│  📋 PLANIFICACIÓN MENSUAL                                 │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Usuario: [Juan Pérez TAE        ▼]                      │
│  Período: [Febrero 2026          ▼]                      │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ IMPLEMENTACIÓN INTERNA SIO                       │    │
│  ├────────────────┬──────┬──────┬──────┬──────┬────┤    │
│  │ Actividad      │Ciclo1│Ciclo2│Ciclo3│Ciclo4│Tot │    │
│  ├────────────────┼──────┼──────┼──────┼──────┼────┤    │
│  │ Formato riesgos│  [4] │  [5] │  [6] │  [6] │ 21 │    │
│  │ Caminatas Ger. │  [1] │  [1] │  [1] │  [1] │  4 │    │
│  │ Inspecciones   │  [2] │  [2] │  [2] │  [2] │  8 │    │
│  └────────────────┴──────┴──────┴──────┴──────┴────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ SISTEMA DE EMERGENCIAS                           │    │
│  │ [Collapsed - Click to expand]                    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  [Guardar Borrador]  [Aprobar y Notificar]              │
└──────────────────────────────────────────────────────────┘
```

### 8.3 Registro de Ejecución

```
┌──────────────────────────────────────────────────────────┐
│  ✅ REGISTRAR EJECUCIÓN                                  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Actividad: Diligenciar formato de riesgos              │
│  Categoría: Implementación Interna SIO                   │
│  Fecha: 25/01/2026 10:30 AM                              │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Estado:  ⚫ Completado                           │    │
│  │          ○ Pendiente                             │    │
│  │          ○ Con Novedad                           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  Observaciones:                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Formato diligenciado correctamente.              │    │
│  │ Se recordaron riesgos en zona de cargue.         │    │
│  │ 15 trabajadores capacitados.                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  📎 Evidencias:                                          │
│  [+ Subir Archivo]                                       │
│  📷 foto_1.jpg (2.3 MB) [x]                              │
│  📄 formato_firmado.pdf (1.1 MB) [x]                     │
│                                                           │
│  [Cancelar]  [Guardar]                                   │
└──────────────────────────────────────────────────────────┘
```

---

## 9. SEGURIDAD

### 9.1 Autenticación

- JWT con expiración de 30 minutos
- Refresh tokens con 7 días de validez
- 2FA obligatorio para Administradores (TOTP)
- Bloqueo tras 5 intentos fallidos

### 9.2 Autorización

**Matriz de Permisos:**

| Funcionalidad | Admin | Coord | Superv | TAE | Empleado |
|---------------|-------|-------|--------|-----|----------|
| Crear usuarios | ✅ | ❌ | ❌ | ❌ | ❌ |
| Crear planes | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ejecutar actividades | ✅ | ✅ | ✅ | ✅ | ❌ |
| Aprobar ejecuciones | ✅ | ✅ | ✅
