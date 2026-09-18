"""
Seed data para el Sistema de Gestión de Seguridad Industrial.
Contiene 10 categorías y 53 actividades del catálogo vigente.
"""

# ============================================
# CATEGORÍAS DE ACTIVIDADES (10 categorías)
# ============================================

ACTIVITY_CATEGORIES = [
    {
        "code": "PLAN_DE_DESARROLLO",
        "name": "PLAN DE DESARROLLO",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: PLAN DE DESARROLLO.",
        "display_order": 1,
        "color": "#faad14",
        "icon": "StarOutlined"
    },
    {
        "code": "OPERACIONAL",
        "name": "OPERACIONAL",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: OPERACIONAL.",
        "display_order": 2,
        "color": "#52c41a",
        "icon": "ScheduleOutlined"
    },
    {
        "code": "PRIMEROS_AUXILIOS",
        "name": "PRIMEROS AUXILIOS",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: PRIMEROS AUXILIOS.",
        "display_order": 3,
        "color": "#fa541c",
        "icon": "MedicineBoxOutlined"
    },
    {
        "code": "ALCOHOL_Y_DROGAS",
        "name": "ALCOHOL Y DROGAS",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: ALCOHOL Y DROGAS.",
        "display_order": 4,
        "color": "#722ed1",
        "icon": "ExperimentOutlined"
    },
    {
        "code": "INTEGRIDAD_OPERACIONAL",
        "name": "INTEGRIDAD OPERACIONAL",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: INTEGRIDAD OPERACIONAL.",
        "display_order": 5,
        "color": "#1890ff",
        "icon": "SafetyOutlined"
    },
    {
        "code": "ENTRENAMIENTO",
        "name": "ENTRENAMIENTO",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: ENTRENAMIENTO.",
        "display_order": 6,
        "color": "#13c2c2",
        "icon": "BookOutlined"
    },
    {
        "code": "ASEGURAMIENTO",
        "name": "ASEGURAMIENTO",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: ASEGURAMIENTO.",
        "display_order": 7,
        "color": "#eb2f96",
        "icon": "CheckCircleOutlined"
    },
    {
        "code": "SALUD_Y_SEGURIDAD",
        "name": "SALUD Y SEGURIDAD",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: SALUD Y SEGURIDAD.",
        "display_order": 8,
        "color": "#ff4d4f",
        "icon": "AlertOutlined"
    },
    {
        "code": "PROCESOS",
        "name": "PROCESOS",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: PROCESOS.",
        "display_order": 9,
        "color": "#2f54eb",
        "icon": "ToolOutlined"
    },
    {
        "code": "SOPORTE_A_PRODUCCION",
        "name": "SOPORTE A PRODUCCION",
        "description": "Categoría importada desde el Excel PLAN DE TRABAJO JAGUARES 2026: SOPORTE A PRODUCCION.",
        "display_order": 10,
        "color": "#fa8c16",
        "icon": "CarryOutOutlined"
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
# PLANTILLAS DE ACTIVIDADES (53 actividades)
# ============================================

ACTIVITY_TEMPLATES = [
    # ==========================================
    # PLAN DE DESARROLLO (2 actividades)
    # ==========================================
    {"category_code": "PLAN_DE_DESARROLLO", "code": "PLAN_DE_DESARROLLO-001", "name": "Actualizar tablero de indicador de desempeño individual", "description": "Actualizar tablero de indicador de desempeño individual", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "PLAN_DE_DESARROLLO", "code": "PLAN_DE_DESARROLLO-002", "name": "Reunion de PDI", "description": "Reunion de PDI", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    # ==========================================
    # OPERACIONAL (9 actividades)
    # ==========================================
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-001", "name": "Asistencia a reunión diaria (G-COM)", "description": "Asistencia a reunión diaria (G-COM)", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-002", "name": "Auditoría de SSI en equipo Minero", "description": "Auditoría de SSI en equipo Minero", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-003", "name": "Entrega de extintores.", "description": "Entrega de extintores.", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-004", "name": "Entregas de equipo a taller", "description": "Entregas de equipo a taller", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-005", "name": "Actualizar informe de disponibilidad diaria de las Unidades de Emergencia.", "description": "Actualizar informe de disponibilidad diaria de las Unidades de Emergencia.", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 5},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-006", "name": "Envio de Informe de faltantes de la máquina (Inventario)", "description": "Envio de Informe de faltantes de la máquina (Inventario)", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 6},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-007", "name": "Mantenimiento de unidades de emergencia", "description": "Mantenimiento de unidades de emergencia", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 7},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-008", "name": "Organizar esquema de emergencia", "description": "Organizar esquema de emergencia", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 8},
    {"category_code": "OPERACIONAL", "code": "OPERACIONAL-009", "name": "Participacion de Simulacros", "description": "Participacion de Simulacros", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 9},
    # ==========================================
    # PRIMEROS AUXILIOS (4 actividades)
    # ==========================================
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PRIMEROS_AUXILIOS-001", "name": "Carta Orden", "description": "Carta Orden", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PRIMEROS_AUXILIOS-002", "name": "Curaciones", "description": "Curaciones", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PRIMEROS_AUXILIOS-003", "name": "Atension de paciente en CAE - Primeros Auxilios / Medicamentos, Toma de signos", "description": "Atension de paciente en CAE - Primeros Auxilios / Medicamentos, Toma de signos", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "PRIMEROS_AUXILIOS", "code": "PRIMEROS_AUXILIOS-004", "name": "Remisiones / traslado a EPS", "description": "Remisiones / traslado a EPS", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 4},
    # ==========================================
    # ALCOHOL Y DROGAS (4 actividades)
    # ==========================================
    {"category_code": "ALCOHOL_Y_DROGAS", "code": "ALCOHOL_Y_DROGAS-001", "name": "Citacion de Alcohol y Drogas", "description": "Citacion de Alcohol y Drogas", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "ALCOHOL_Y_DROGAS", "code": "ALCOHOL_Y_DROGAS-002", "name": "Enviar informe de resultados de Alcohol y  Drogas", "description": "Enviar informe de resultados de Alcohol y  Drogas", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    {"category_code": "ALCOHOL_Y_DROGAS", "code": "ALCOHOL_Y_DROGAS-003", "name": "Mantener actualizado tablero de muestreo de A&D", "description": "Mantener actualizado tablero de muestreo de A&D", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "ALCOHOL_Y_DROGAS", "code": "ALCOHOL_Y_DROGAS-004", "name": "Realizacion de Muestreo de Alcohol y  Drogas", "description": "Realizacion de Muestreo de Alcohol y  Drogas", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 4},
    # ==========================================
    # INTEGRIDAD OPERACIONAL (5 actividades)
    # ==========================================
    {"category_code": "INTEGRIDAD_OPERACIONAL", "code": "INTEGRIDAD_OPERACIONAL-001", "name": "Diligenciar formato de recordacion de riesgos en atencion de emergencias", "description": "Diligenciar formato de recordacion de riesgos en atencion de emergencias", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "INTEGRIDAD_OPERACIONAL", "code": "INTEGRIDAD_OPERACIONAL-002", "name": "Diligenciar Formato de Recordacion de Riesgos en la Conduccion", "description": "Diligenciar Formato de Recordacion de Riesgos en la Conduccion", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    {"category_code": "INTEGRIDAD_OPERACIONAL", "code": "INTEGRIDAD_OPERACIONAL-003", "name": "No. Inspecciones SIO", "description": "No. Inspecciones SIO", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "INTEGRIDAD_OPERACIONAL", "code": "INTEGRIDAD_OPERACIONAL-004", "name": "No. Observaciones de Conduccion de Equipos Liviano/Mediano y/o evaluacion", "description": "No. Observaciones de Conduccion de Equipos Liviano/Mediano y/o evaluacion", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "INTEGRIDAD_OPERACIONAL", "code": "INTEGRIDAD_OPERACIONAL-005", "name": "No. Observaciones de Tareas Criticas", "description": "No. Observaciones de Tareas Criticas", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 5},
    # ==========================================
    # ENTRENAMIENTO (11 actividades)
    # ==========================================
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-001", "name": "Entrenamiento de Conductores de Ambulancia", "description": "Entrenamiento de Conductores de Ambulancia", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-002", "name": "Entrenamiento en Conexión a Tanquero/hidrante", "description": "Entrenamiento en Conexión a Tanquero/hidrante", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-003", "name": "Entrenamiento en Kit de Trauma", "description": "Entrenamiento en Kit de Trauma", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-004", "name": "Entrenamiento en Postura Arnes", "description": "Entrenamiento en Postura Arnes", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-005", "name": "Entrenamiento en Postura EPP Linea de Fuego (Incluye air pack)", "description": "Entrenamiento en Postura EPP Linea de Fuego (Incluye air pack)", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 5},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-006", "name": "Entrenamiento en RCP", "description": "Entrenamiento en RCP", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 6},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-007", "name": "Entrenamiento en Rescate (nudos y sistemas de Anclaje)", "description": "Entrenamiento en Rescate (nudos y sistemas de Anclaje)", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 7},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-008", "name": "Entrenamiento en seguridad básica", "description": "Entrenamiento en seguridad básica", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 8},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-009", "name": "Entrenamiento Lanzamiento de Linea de Vida", "description": "Entrenamiento Lanzamiento de Linea de Vida", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 9},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-010", "name": "Entrenamiento mensual TAEs", "description": "Entrenamiento mensual TAEs", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 10},
    {"category_code": "ENTRENAMIENTO", "code": "ENTRENAMIENTO-011", "name": "Estudio de normas NFPA", "description": "Estudio de normas NFPA", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 11},
    # ==========================================
    # ASEGURAMIENTO (9 actividades)
    # ==========================================
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-001", "name": "Inspeccion de CAE", "description": "Inspeccion de CAE", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-002", "name": "Inspeccion de Tanqueros", "description": "Inspeccion de Tanqueros", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-003", "name": "Inspección de Vias y ubicacion de Equipos de Cargue", "description": "Inspección de Vias y ubicacion de Equipos de Cargue", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-004", "name": "Inspeccion preoperacional Ambulancia", "description": "Inspeccion preoperacional Ambulancia", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-005", "name": "Inspeccion preoperacional de Maquina de bomberos", "description": "Inspeccion preoperacional de Maquina de bomberos", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 5},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-006", "name": "Inspeccion Unidad Hazmat", "description": "Inspeccion Unidad Hazmat", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 6},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-007", "name": "Recepcion de Reportes de Tareas Criticas / Lejanas", "description": "Recepcion de Reportes de Tareas Criticas / Lejanas", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 7},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-008", "name": "Revision SSI/SCI, post Activacion", "description": "Revision SSI/SCI, post Activacion", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 8},
    {"category_code": "ASEGURAMIENTO", "code": "ASEGURAMIENTO-009", "name": "Verificar Aseo de Ambulancias por Aseocolba", "description": "Verificar Aseo de Ambulancias por Aseocolba", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 9},
    # ==========================================
    # SALUD Y SEGURIDAD (2 actividades)
    # ==========================================
    {"category_code": "SALUD_Y_SEGURIDAD", "code": "SALUD_Y_SEGURIDAD-001", "name": "Reportes de Accidentes de Trabajo", "description": "Reportes de Accidentes de Trabajo", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "SALUD_Y_SEGURIDAD", "code": "SALUD_Y_SEGURIDAD-002", "name": "Reporte de actividades fisicas  (Cerrejon en movimiento, Pausas activas, Actividad fisica en Entrenamiento, Actividad fisica Particulares)", "description": "Reporte de actividades fisicas  (Cerrejon en movimiento, Pausas activas, Actividad fisica en Entrenamiento, Actividad fisica Particulares)", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    # ==========================================
    # PROCESOS (2 actividades)
    # ==========================================
    {"category_code": "PROCESOS", "code": "PROCESOS-001", "name": "Seguimiento Proceso", "description": "Seguimiento Proceso", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "PROCESOS", "code": "PROCESOS-002", "name": "Seguimiento Soporte de Proceso", "description": "Seguimiento Soporte de Proceso", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    # ==========================================
    # SOPORTE A PRODUCCION (5 actividades)
    # ==========================================
    {"category_code": "SOPORTE_A_PRODUCCION", "code": "SOPORTE_A_PRODUCCION-001", "name": "Soporte a Pacientes Incapacitados (Taxi/Hotel)", "description": "Soporte a Pacientes Incapacitados (Taxi/Hotel)", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 1},
    {"category_code": "SOPORTE_A_PRODUCCION", "code": "SOPORTE_A_PRODUCCION-002", "name": "Soporte en Cargue de Material Caliente", "description": "Soporte en Cargue de Material Caliente", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 2},
    {"category_code": "SOPORTE_A_PRODUCCION", "code": "SOPORTE_A_PRODUCCION-003", "name": "Soporte en Empuje de Material Caliente", "description": "Soporte en Empuje de Material Caliente", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 3},
    {"category_code": "SOPORTE_A_PRODUCCION", "code": "SOPORTE_A_PRODUCCION-004", "name": "Soporte en Perforacion de Pozos Calientes", "description": "Soporte en Perforacion de Pozos Calientes", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 4},
    {"category_code": "SOPORTE_A_PRODUCCION", "code": "SOPORTE_A_PRODUCCION-005", "name": "Soprte a cargue de pozo en caliente", "description": "Soprte a cargue de pozo en caliente", "requires_evidence": False, "is_critical": False, "default_frequency": 1, "display_order": 5},
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
