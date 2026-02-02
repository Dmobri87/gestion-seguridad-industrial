from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ComplianceMetric(Base):
    """
    Métricas de cumplimiento calculadas automáticamente.
    Se actualizan cuando se registran ejecuciones.
    """
    __tablename__ = "compliance_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Período
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)

    # Categoría de actividad (opcional, para métricas por categoría)
    category_id = Column(Integer, ForeignKey("activity_categories.id"), nullable=True)

    # Métricas
    total_planned = Column(Integer, default=0)
    total_executed = Column(Integer, default=0)
    compliance_percentage = Column(Float, default=0.0)

    # Desglose por ciclo
    cycle_1_planned = Column(Integer, default=0)
    cycle_1_executed = Column(Integer, default=0)
    cycle_2_planned = Column(Integer, default=0)
    cycle_2_executed = Column(Integer, default=0)
    cycle_3_planned = Column(Integer, default=0)
    cycle_3_executed = Column(Integer, default=0)
    cycle_4_planned = Column(Integer, default=0)
    cycle_4_executed = Column(Integer, default=0)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MonthlySummary(Base):
    """
    Resumen mensual consolidado.
    Se genera al final de cada mes para snapshot histórico.
    """
    __tablename__ = "monthly_summaries"

    id = Column(Integer, primary_key=True, index=True)

    # Período
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # KPIs principales
    total_accidents = Column(Integer, default=0)  # Número de accidentes
    total_emergencies = Column(Integer, default=0)  # Emergencias atendidas
    avg_response_time = Column(Float, nullable=True)  # Tiempo promedio de respuesta

    # Cumplimiento general
    total_planned_activities = Column(Integer, default=0)
    total_executed_activities = Column(Integer, default=0)
    overall_compliance = Column(Float, default=0.0)

    # Cumplimiento por categoría (JSON)
    compliance_by_category = Column(Text, nullable=True)  # JSON con % por categoría

    # Personal
    active_employees = Column(Integer, default=0)
    employees_with_expired_certs = Column(Integer, default=0)

    # Equipos
    total_equipment = Column(Integer, default=0)
    equipment_in_maintenance = Column(Integer, default=0)
    equipment_out_of_service = Column(Integer, default=0)

    # Certificaciones
    expiring_certs_30_days = Column(Integer, default=0)
    expired_certs = Column(Integer, default=0)

    # Notas
    notes = Column(Text, nullable=True)

    # Generado por
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnnualSummary(Base):
    """
    Resumen anual consolidado.
    """
    __tablename__ = "annual_summaries"

    id = Column(Integer, primary_key=True, index=True)

    # Año
    year = Column(Integer, nullable=False, index=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # KPIs anuales
    total_accidents = Column(Integer, default=0)
    total_emergencies = Column(Integer, default=0)
    avg_response_time = Column(Float, nullable=True)

    # Cumplimiento general
    overall_compliance = Column(Float, default=0.0)

    # Cumplimiento por mes (JSON)
    compliance_by_month = Column(Text, nullable=True)  # JSON con % por mes

    # Cumplimiento por categoría (JSON)
    compliance_by_category = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Accident(Base):
    """
    KPI principal: Registro de accidentes laborales.
    El objetivo es mantener esto en CERO.
    """
    __tablename__ = "accidents"

    id = Column(Integer, primary_key=True, index=True)

    # Código único
    accident_code = Column(String(50), unique=True, nullable=False, index=True)

    # Fecha y hora
    accident_date = Column(DateTime(timezone=True), nullable=False)

    # Tipo de accidente
    accident_type = Column(String(100), nullable=False)

    # Descripción
    description = Column(Text, nullable=False)

    # Ubicación
    location = Column(String(255), nullable=True)

    # Persona afectada (si aplica)
    affected_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    external_affected_name = Column(String(255), nullable=True)  # Si no es empleado

    # Severidad
    severity = Column(String(50), nullable=False)  # Leve, Moderado, Grave, Fatal

    # Días perdidos
    lost_days = Column(Integer, default=0)

    # Investigación
    root_cause = Column(Text, nullable=True)
    corrective_actions = Column(Text, nullable=True)
    preventive_actions = Column(Text, nullable=True)

    # Estado
    status = Column(String(50), default="Abierto")  # Abierto, En Investigación, Cerrado

    # Reportado por
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Departamento
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)


class SavedReport(Base):
    """
    Reportes guardados por usuarios.
    """
    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario propietario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Nombre y descripción
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Tipo de reporte
    report_type = Column(String(100), nullable=False)

    # Configuración del reporte (JSON)
    configuration = Column(Text, nullable=False)  # Filtros, columnas, etc.

    # Compartido
    is_public = Column(Boolean, default=False)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScheduledReport(Base):
    """
    Reportes programados para envío automático.
    """
    __tablename__ = "scheduled_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Reporte base
    saved_report_id = Column(Integer, ForeignKey("saved_reports.id"), nullable=False)

    # Frecuencia
    frequency = Column(String(50), nullable=False)  # daily, weekly, monthly

    # Día/hora de envío
    send_day = Column(Integer, nullable=True)  # Día del mes o día de la semana
    send_time = Column(String(10), nullable=True)  # HH:MM

    # Destinatarios (JSON array de emails)
    recipients = Column(Text, nullable=False)

    # Formato
    format = Column(String(20), default="pdf")  # pdf, excel

    # Estado
    is_active = Column(Boolean, default=True)

    # Última ejecución
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    next_send_at = Column(DateTime(timezone=True), nullable=True)

    # Creado por
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    """
    Log de auditoría completo del sistema.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario que realizó la acción
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)  # Backup en caso de usuario eliminado

    # Acción
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type = Column(String(100), nullable=False)  # users, plans, executions, etc.
    resource_id = Column(Integer, nullable=True)

    # Detalles
    description = Column(Text, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON

    # Request info
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
