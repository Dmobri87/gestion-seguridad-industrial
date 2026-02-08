"""
Seed data para el Sistema de Gestión de Seguridad Industrial.
Contiene las 8 categorías y 93+ actividades extraídas del Excel.
"""

# ============================================
# CATEGORÍAS DE ACTIVIDADES (8 categorías)
# ============================================

ACTIVITY_CATEGORIES = [
    {
        "code": "SIO",
        "name": "IMPLEMENTACIÓN INTERNA SIO",
        "description": "Actividades relacionadas con el Sistema Integrado de Operaciones",
        "display_order": 1,
        "color": "#1890ff",
        "icon": "SafetyOutlined"
    },
    {
        "code": "EMERGENCIAS",
        "name": "SISTEMA DE EMERGENCIAS",
        "description": "Registro y seguimiento de emergencias atendidas",
        "display_order": 2,
        "color": "#ff4d4f",
        "icon": "AlertOutlined"
    },
    {
        "code": "PROGRAMA_TAE",
        "name": "PROGRAMA DE ACTIVIDADES DEL TAE",
        "description": "Actividades operativas del Técnico de Atención de Emergencias",
        "display_order": 3,
        "color": "#52c41a",
        "icon": "ScheduleOutlined"
    },
    {
        "code": "PRIMEROS_AUXILIOS",
        "name": "ATENCIÓN PRIMEROS AUXILIOS",
        "description": "Actividades relacionadas con atención médica y primeros auxilios",
        "display_order": 4,
        "color": "#fa8c16",
        "icon": "MedicineBoxOutlined"
    },
    {
        "code": "ENTRENAMIENTO",
        "name": "ENTRENAMIENTO",
        "description": "Capacitaciones y entrenamientos recibidos",
        "display_order": 5,
        "color": "#722ed1",
        "icon": "BookOutlined"
    },
    {
        "code": "ENTRENAMIENTO_DICTAR",
        "name": "ENTRENAMIENTOS A DICTAR POR EL TAE",
        "description": "Capacitaciones impartidas por el TAE a terceros",
        "display_order": 6,
        "color": "#13c2c2",
        "icon": "TeamOutlined"
    },
    {
        "code": "PROCESOS",
        "name": "PLAN DE ACTIVIDADES POR PROCESOS",
        "description": "Actividades de mantenimiento e inspección de equipos",
        "display_order": 7,
        "color": "#eb2f96",
        "icon": "ToolOutlined"
    },
    {
        "code": "PDI",
        "name": "PLAN DE ACTIVIDADES PDI",
        "description": "Plan de Desarrollo Individual",
        "display_order": 8,
        "color": "#faad14",
        "icon": "StarOutlined"
    },
]

# ============================================
# TIPOS DE EMERGENCIAS (para el módulo de emergencias)
# ============================================

EMERGENCY_TYPES = [
    {
        "code": "LESION_AL",
        "name": "Lesión AL (Accidente Laboral)",
        "description": "Lesiones ocurridas durante actividades laborales",
        "default_severity": "Alta",
        "requires_immediate_response": True,
        "target_response_time": 5,
        "color": "#ff4d4f",
        "display_order": 1
    },
    {
        "code": "CONATO_INCENDIO",
        "name": "Conato de incendio",
        "description": "Inicio de incendio controlable",
        "default_severity": "Alta",
        "requires_immediate_response": True,
        "target_response_time": 3,
        "color": "#ff7a45",
        "display_order": 2
    },
    {
        "code": "DANOS_PROPIEDAD",
        "name": "Daños a propiedad",
        "description": "Daños materiales a instalaciones o equipos",
        "default_severity": "Media",
        "requires_immediate_response": False,
        "target_response_time": 15,
        "color": "#ffc53d",
        "display_order": 3
    },
    {
        "code": "ENFERMEDAD_GENERAL",
        "name": "Enfermedad general",
        "description": "Atención médica por enfermedad no laboral",
        "default_severity": "Media",
        "requires_immediate_response": True,
        "target_response_time": 10,
        "color": "#40a9ff",
        "display_order": 4
    },
    {
        "code": "IMPACTO_AMBIENTAL",
        "name": "Impacto ambiental",
        "description": "Eventos con afectación al medio ambiente",
        "default_severity": "Alta",
        "requires_immediate_response": True,
        "target_response_time": 10,
        "color": "#73d13d",
        "display_order": 5
    },
    {
        "code": "ATENCION_COMUNIDAD",
        "name": "Atención a comunidad",
        "description": "Atención de emergencias en comunidades cercanas",
        "default_severity": "Media",
        "requires_immediate_response": True,
        "target_response_time": 15,
        "color": "#9254de",
        "display_order": 6
    },
    {
        "code": "INCIDENTE_DEPORTIVO",
        "name": "Incidente deportivo",
        "description": "Lesiones durante actividades deportivas",
        "default_severity": "Baja",
        "requires_immediate_response": True,
        "target_response_time": 10,
        "color": "#36cfc9",
        "display_order": 7
    },
    {
        "code": "NO_CLASIFICADO",
        "name": "No clasificado",
        "description": "Emergencias que no corresponden a otras categorías",
        "default_severity": "Media",
        "requires_immediate_response": True,
        "target_response_time": 15,
        "color": "#bfbfbf",
        "display_order": 8
    },
]

# ============================================
# PLANTILLAS DE ACTIVIDADES (93+ actividades)
# ============================================

ACTIVITY_TEMPLATES = [
    # ==========================================
    # 1. IMPLEMENTACIÓN INTERNA SIO (11 actividades)
    # ==========================================
    {"category_code": "SIO", "code": "SIO-001", "name": "Diligenciar formato de recordación de riesgos en atención de emergencias", "requires_evidence": True, "is_critical": False, "default_frequency": 5, "display_order": 1},
    {"category_code": "SIO", "code": "SIO-002", "name": "Diligenciar formato de recordación de riesgos en la conducción", "requires_evidence": True, "is_critical": False, "default_frequency": 2, "display_order": 2},
    {"category_code": "SIO", "code": "SIO-003", "name": "No. Caminatas Gerenciales", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "SIO", "code": "SIO-004", "name": "No. Inspecciones SIO", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "SIO", "code": "SIO-005", "name": "No. Observaciones de Conducción de Equipos Liviano/Mediano", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 5},
    {"category_code": "SIO", "code": "SIO-006", "name": "No. Observaciones de Tareas Críticas (4 Mensuales)", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 6},
    {"category_code": "SIO", "code": "SIO-007", "name": "No. Observaciones PPABC", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 7},
    {"category_code": "SIO", "code": "SIO-008", "name": "No. Reporte CAS (Cada TAE Realizará 1 Reporte por Trimestre) y verificación de su cierre", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 8},
    {"category_code": "SIO", "code": "SIO-009", "name": "Observación de tercero a TAEs en la conducción de equipo mediano", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 9},
    {"category_code": "SIO", "code": "SIO-010", "name": "No. Reuniones de Comité de Seguridad", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 10},

    # ==========================================
    # 2. SISTEMA DE EMERGENCIAS (9 actividades - métricas)
    # ==========================================
    {"category_code": "EMERGENCIAS", "code": "EMG-001", "name": "No. de emergencias por lesión atendidas AL", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 1},
    {"category_code": "EMERGENCIAS", "code": "EMG-002", "name": "No. de emergencias por conato atendidas", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 2},
    {"category_code": "EMERGENCIAS", "code": "EMG-003", "name": "No. de emergencias o reportes por DAÑOS", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 3},
    {"category_code": "EMERGENCIAS", "code": "EMG-004", "name": "No. Emergencias por enfermedad general", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 4},
    {"category_code": "EMERGENCIAS", "code": "EMG-005", "name": "No. de emergencias o reportes por impacto ambiental", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 5},
    {"category_code": "EMERGENCIAS", "code": "EMG-006", "name": "No. de emergencias atendidas a comunidad", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 6},
    {"category_code": "EMERGENCIAS", "code": "EMG-007", "name": "Incidentes deportivos", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 7},
    {"category_code": "EMERGENCIAS", "code": "EMG-008", "name": "No Clasificados", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 8},

    # ==========================================
    # 3. PROGRAMA DE ACTIVIDADES DEL TAE (35 actividades)
    # ==========================================
    {"category_code": "PROGRAMA_TAE", "code": "TAE-001", "name": "Actualización de bitácora", "requires_evidence": False, "is_critical": False, "default_frequency": 7, "display_order": 1},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-002", "name": "Aseo de Ambulancias por Aseocolba", "requires_evidence": False, "is_critical": False, "default_frequency": 2, "display_order": 2},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-003", "name": "Asistencia a reunión de miembros de un CAE", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-004", "name": "Asistencia a reunión general de coordinadores", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-005", "name": "Auditoría de SSI en equipo Minero", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 5},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-006", "name": "Cantidad de horas en el cargue de material caliente", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 6},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-007", "name": "Coordinar los pedidos de Medicamentos e Insumos y su distribución a los CAEs", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 7},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-008", "name": "Cumplir estándar de entregas de equipo a taller", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 8},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-009", "name": "Entrevista con psicóloga", "requires_evidence": False, "is_critical": False, "default_frequency": 0, "display_order": 9},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-010", "name": "Entrevista de PDI", "requires_evidence": False, "is_critical": False, "default_frequency": 0, "display_order": 10},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-011", "name": "Enviar informe de disponibilidad diaria de las Unidades de Emergencia y los Kilometrajes / Horómetros fin de semana", "requires_evidence": True, "is_critical": False, "default_frequency": 7, "display_order": 11},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-012", "name": "Envío de Informe de faltantes de la máquina", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 12},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-013", "name": "Inspección de Tanqueros", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 13},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-014", "name": "Inspección funcionamiento SSI luego de activación", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 14},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-015", "name": "Inspección preoperacional", "requires_evidence": True, "is_critical": False, "default_frequency": 7, "display_order": 15},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-016", "name": "Inspección y ubicación de equipos (Recorrido cada tercer día)", "requires_evidence": True, "is_critical": False, "default_frequency": 2, "display_order": 16},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-017", "name": "Inspecciones de Riesgos", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 17},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-018", "name": "Inventario de dotación de Ambulancias", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 18},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-019", "name": "Mantener actualizado tablero de indicador de desempeño individual y asegurar el soporte documental de sus actividades", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 19},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-020", "name": "Mantener unidades de emergencia asignados debidamente taqueados de combustible y agua", "requires_evidence": False, "is_critical": False, "default_frequency": 7, "display_order": 20},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-021", "name": "Mantenimiento de boquillas, accesorios CI y monitor", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 21},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-022", "name": "Mantenimiento de unidades de emergencia (Hacer Equipo con Bomberos)", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 22},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-023", "name": "Medición de caudales en las Bombas de máquinas contra incendio", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 23},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-024", "name": "Mediciones de gases", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 24},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-025", "name": "Número de servicios de Prevención en Cargue de Material en Caliente", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 25},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-026", "name": "Observación de tareas externas respecto de atención de emergencias", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 26},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-027", "name": "Participación en Simulacros", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 27},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-028", "name": "Prueba de calidad de espuma contra incendio", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 28},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-029", "name": "Verificación del sistema de Espuma de las máquinas contraincendio", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 29},
    {"category_code": "PROGRAMA_TAE", "code": "TAE-030", "name": "Verificación Tanqueros", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 30},

    # ==========================================
    # 4. ATENCIÓN PRIMEROS AUXILIOS (10 actividades)
    # ==========================================
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-001", "name": "Carta Orden", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 1},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-002", "name": "Citación a Muestreo de A&D", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 2},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-003", "name": "Curaciones", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 3},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-004", "name": "Evacuaciones", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 4},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-005", "name": "Inyectología", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 5},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-006", "name": "Primeros Auxilios", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 6},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-007", "name": "Realización de pruebas de A&D", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 7},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-008", "name": "Remisión EPS", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 8},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PA-009", "name": "Soporte a pacientes incapacitados (hotel, transporte)", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 9},

    # ==========================================
    # 5. ENTRENAMIENTO (11 actividades)
    # ==========================================
    {"category_code": "ENTRENAMIENTO", "code": "ENT-001", "name": "Certificación de trabajo de altura", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 1},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-002", "name": "Entrenamiento en Conexión a Tanquero/hidrante", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 2},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-003", "name": "Entrenamiento en Postura Arnés", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 3},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-004", "name": "Entrenamiento en Postura EPP Línea de Fuego (Incluye air pack)", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 4},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-005", "name": "Entrenamiento en Rescate (nudos y sistemas de Anclaje)", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 5},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-006", "name": "Proceso de obtención Pase gris", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 6},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-007", "name": "Entrenamiento en seguridad básica", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 7},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-008", "name": "Entrenamiento mensual TAEs", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 8},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-009", "name": "Estudio de normas NFPA", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 9},
    {"category_code": "ENTRENAMIENTO", "code": "ENT-010", "name": "Mantener actualizado refresco de muestreo de A&D", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 10},

    # ==========================================
    # 6. ENTRENAMIENTOS A DICTAR POR EL TAE (3 actividades)
    # ==========================================
    {"category_code": "ENTRENAMIENTO_DICTAR", "code": "DICT-001", "name": "Entrenamiento a terceros para conducir ambulancia (Certificación de Conductores)", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 1},
    {"category_code": "ENTRENAMIENTO_DICTAR", "code": "DICT-002", "name": "Entrenamiento descenso líneas de vida", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 2},
    {"category_code": "ENTRENAMIENTO_DICTAR", "code": "DICT-003", "name": "Brigadistas Entrenados en CAE", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 3},

    # ==========================================
    # 7. PLAN DE ACTIVIDADES POR PROCESOS (22 actividades)
    # ==========================================
    {"category_code": "PROCESOS", "code": "PROC-001", "name": "Cambio de Batería a los controles de los monitores de las máquinas contraincendio", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 1},
    {"category_code": "PROCESOS", "code": "PROC-002", "name": "Inspección de ARNESES", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 2},
    {"category_code": "PROCESOS", "code": "PROC-003", "name": "Inspección de Bombas CI", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 3},
    {"category_code": "PROCESOS", "code": "PROC-004", "name": "Inspección de escaleras", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "PROCESOS", "code": "PROC-005", "name": "Inspección de guardas", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 5},
    {"category_code": "PROCESOS", "code": "PROC-006", "name": "Inventario de equipos SCBA", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 6},
    {"category_code": "PROCESOS", "code": "PROC-007", "name": "Mantenimiento correctivo SCBA", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 7},
    {"category_code": "PROCESOS", "code": "PROC-008", "name": "Mantenimiento preventivo SCBA (cambio aire, revisión arneses y PH, baterías y aseo general)", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 8},
    {"category_code": "PROCESOS", "code": "PROC-009", "name": "Mantenimiento de equipos menores", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 9},
    {"category_code": "PROCESOS", "code": "PROC-010", "name": "Inspección mensual y prueba de equipos menores", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 10},
    {"category_code": "PROCESOS", "code": "PROC-011", "name": "Control de Inventarios y Funcionamientos de los radios", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 11},
    {"category_code": "PROCESOS", "code": "PROC-012", "name": "Medición de Caudales en las Bombas CI", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 12},
    {"category_code": "PROCESOS", "code": "PROC-013", "name": "Realización de Pruebas Posicheck", "requires_evidence": True, "is_critical": False, "default_frequency": 1, "display_order": 13},
    {"category_code": "PROCESOS", "code": "PROC-014", "name": "Testado de Mangueras", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 14},
    {"category_code": "PROCESOS", "code": "PROC-015", "name": "Toma de Tiempos de respuesta desde los CAEs", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 15},
    {"category_code": "PROCESOS", "code": "PROC-016", "name": "Verificación del Vencimiento autorizaciones conducción", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 16},
    {"category_code": "PROCESOS", "code": "PROC-017", "name": "Verificación del Vencimiento SOAT", "requires_evidence": True, "is_critical": True, "default_frequency": 1, "display_order": 17},
    {"category_code": "PROCESOS", "code": "PROC-018", "name": "Medición de calidad de aire Sistema SCBA", "requires_evidence": True, "is_critical": True, "default_frequency": 0, "display_order": 18},
    {"category_code": "PROCESOS", "code": "PROC-019", "name": "Medición de Índice de Masa Corporal", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 19},

    # ==========================================
    # 8. PLAN DE ACTIVIDADES PDI (4 actividades - típicamente específicas)
    # ==========================================
    {"category_code": "PDI", "code": "PDI-001", "name": "Actividad PDI 1", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 1},
    {"category_code": "PDI", "code": "PDI-002", "name": "Actividad PDI 2", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 2},
    {"category_code": "PDI", "code": "PDI-003", "name": "Actividad PDI 3", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 3},
    {"category_code": "PDI", "code": "PDI-004", "name": "Actividad PDI 4", "requires_evidence": True, "is_critical": False, "default_frequency": 0, "display_order": 4},
]

# ============================================
# CATEGORÍAS DE EQUIPOS
# ============================================

EQUIPMENT_CATEGORIES = [
    {"code": "AMBULANCIA", "name": "Ambulancias", "default_maintenance_frequency_days": 30, "icon": "CarOutlined", "color": "#ff4d4f"},
    {"code": "SCBA", "name": "SCBA (Equipos de Respiración Autónoma)", "default_maintenance_frequency_days": 30, "icon": "AlertOutlined", "color": "#1890ff"},
    {"code": "RADIO", "name": "Radios de Comunicación", "default_maintenance_frequency_days": 90, "icon": "WifiOutlined", "color": "#52c41a"},
    {"code": "BOMBA_CI", "name": "Bombas Contra Incendio", "default_maintenance_frequency_days": 30, "icon": "FireOutlined", "color": "#fa8c16"},
    {"code": "TANQUERO", "name": "Tanqueros", "default_maintenance_frequency_days": 30, "icon": "CarOutlined", "color": "#722ed1"},
    {"code": "ARNES", "name": "Arneses y Equipos de Altura", "default_maintenance_frequency_days": 180, "icon": "SafetyOutlined", "color": "#13c2c2"},
    {"code": "ESCALERA", "name": "Escaleras", "default_maintenance_frequency_days": 90, "icon": "VerticalAlignTopOutlined", "color": "#eb2f96"},
    {"code": "MANGUERA", "name": "Mangueras", "default_maintenance_frequency_days": 180, "icon": "ColumnWidthOutlined", "color": "#faad14"},
    {"code": "MENOR", "name": "Equipos Menores", "default_maintenance_frequency_days": 90, "icon": "ToolOutlined", "color": "#bfbfbf"},
]

# ============================================
# TIPOS DE CERTIFICACIONES
# ============================================

CERTIFICATION_TYPES = [
    # Certificaciones de Personal
    {"code": "CERT_ALTURA", "name": "Trabajo en Altura", "applies_to": "personal", "default_validity_days": 365, "is_mandatory": True, "blocks_on_expiry": True},
    {"code": "CERT_CONDUCCION", "name": "Conducción de Ambulancia", "applies_to": "personal", "default_validity_days": 365, "is_mandatory": True, "blocks_on_expiry": True},
    {"code": "CERT_PRIMEROS_AUX", "name": "Primeros Auxilios", "applies_to": "personal", "default_validity_days": 730, "is_mandatory": True, "blocks_on_expiry": False},
    {"code": "CERT_PASE_GRIS", "name": "Pase Gris", "applies_to": "personal", "default_validity_days": 365, "is_mandatory": True, "blocks_on_expiry": True},
    {"code": "CERT_SCBA", "name": "Manejo de SCBA", "applies_to": "personal", "default_validity_days": 365, "is_mandatory": True, "blocks_on_expiry": True},
    {"code": "CERT_ESPACIOS_CONF", "name": "Rescate en Espacios Confinados", "applies_to": "personal", "default_validity_days": 365, "is_mandatory": False, "blocks_on_expiry": False},

    # Documentos de Vehículos
    {"code": "DOC_SOAT", "name": "SOAT", "applies_to": "vehicle", "default_validity_days": 365, "is_mandatory": True, "blocks_on_expiry": True},
    {"code": "DOC_TECNO_MEC", "name": "Revisión Técnico-Mecánica", "applies_to": "vehicle", "default_validity_days": 365, "is_mandatory": True, "blocks_on_expiry": True},
    {"code": "DOC_LICENCIA", "name": "Licencia de Conducción (Conductor Asignado)", "applies_to": "vehicle", "default_validity_days": 3650, "is_mandatory": True, "blocks_on_expiry": True},
]

# ============================================
# ROLES DE USUARIO
# ============================================

USER_ROLES = [
    {"code": "ADMIN", "name": "Administrador", "description": "Control total del sistema"},
    {"code": "COORDINATOR", "name": "Coordinador", "description": "Planificación y reportes"},
    {"code": "SUPERVISOR", "name": "Supervisor", "description": "Aprobaciones y seguimiento"},
    {"code": "TAE", "name": "TAE", "description": "Técnico de Atención de Emergencias - Ejecución y registro"},
    {"code": "EMPLOYEE", "name": "Empleado", "description": "Consulta y reportes personales"},
    {"code": "GUEST", "name": "Invitado", "description": "Solo lectura"},
]


# ============================================
# FUNCION SEED DATABASE
# ============================================

def seed_database():
    """Poblar la base de datos con datos iniciales."""
    from app.core.database import SessionLocal, engine
    from app.models.user import User, Base
    from app.models.activity_category import ActivityCategory
    from app.models.activity_template import ActivityTemplate
    from app.models.emergency import EmergencyType
    from app.core.security import get_password_hash

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing_cats = db.query(ActivityCategory).count()
        if existing_cats == 0:
            for cat_data in ACTIVITY_CATEGORIES:
                cat = ActivityCategory(**cat_data, is_active=True)
                db.add(cat)
            db.commit()
            print(f"Creadas {len(ACTIVITY_CATEGORIES)} categorias")

        existing_types = db.query(EmergencyType).count()
        if existing_types == 0:
            for et_data in EMERGENCY_TYPES:
                et = EmergencyType(**et_data, is_active=True)
                db.add(et)
            db.commit()
            print(f"Creados {len(EMERGENCY_TYPES)} tipos de emergencias")

        existing_templates = db.query(ActivityTemplate).count()
        if existing_templates == 0:
            categories = {c.code: c.id for c in db.query(ActivityCategory).all()}
            for tmpl_data in ACTIVITY_TEMPLATES:
                cat_code = tmpl_data.pop("category_code")
                if cat_code in categories:
                    tmpl = ActivityTemplate(**tmpl_data, category_id=categories[cat_code], is_active=True)
                    db.add(tmpl)
            db.commit()
            print(f"Creadas {len(ACTIVITY_TEMPLATES)} plantillas")

        admin = db.query(User).filter(User.role == "Administrador").first()
        if not admin:
            admin = User(
                email="admin@cerrejon.com",
                hashed_password=get_password_hash("Admin2026"),
                full_name="Administrador Sistema",
                role="Administrador",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("Usuario admin creado: admin@cerrejon.com / Admin2026")

        print("Seed completado exitosamente")
    except Exception as e:
        db.rollback()
        print(f"Error en seed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
