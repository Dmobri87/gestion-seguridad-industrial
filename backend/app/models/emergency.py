from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Float, Time
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class EmergencySeverity(str, enum.Enum):
    """Niveles de severidad de emergencias"""
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"
    CRITICAL = "Crítica"


class EmergencyStatus(str, enum.Enum):
    """Estados de emergencia"""
    REPORTED = "Reportada"
    IN_PROGRESS = "En Atención"
    CONTROLLED = "Controlada"
    CLOSED = "Cerrada"
    ESCALATED = "Escalada"


class EmergencyType(Base):
    """
    Tipos de emergencias predefinidos (los 8 del Excel).
    """
    __tablename__ = "emergency_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Configuración
    default_severity = Column(String(50), default=EmergencySeverity.MEDIUM.value)
    requires_immediate_response = Column(Boolean, default=True)
    target_response_time = Column(Integer, default=15)  # minutos

    # Icono y color para UI
    icon = Column(String(50), nullable=True)
    color = Column(String(20), default="#ff4d4f")  # Hex color

    # Orden de visualización
    display_order = Column(Integer, default=0)

    # Estado
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    emergencies = relationship("Emergency", back_populates="emergency_type")


class Emergency(Base):
    """
    Registro de emergencias.
    """
    __tablename__ = "emergencies"

    id = Column(Integer, primary_key=True, index=True)

    # Tipo de emergencia
    emergency_type_id = Column(Integer, ForeignKey("emergency_types.id"), nullable=False)
    emergency_type = relationship("EmergencyType", back_populates="emergencies")

    # Código único de emergencia
    emergency_code = Column(String(50), unique=True, nullable=False, index=True)  # EMG-2026-0001

    # Información básica
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)

    # Coordenadas
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

    # Severidad
    severity = Column(String(50), default=EmergencySeverity.MEDIUM.value)

    # Estado
    status = Column(String(50), default=EmergencyStatus.REPORTED.value)

    # Tiempos
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
    arrival_at = Column(DateTime(timezone=True), nullable=True)  # Hora de llegada
    controlled_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Tiempo de respuesta calculado (en minutos)
    response_time_minutes = Column(Integer, nullable=True)

    # Personal involucrado
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    attended_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # TAE que atendió
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Detalles de la atención
    actions_taken = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    # Afectados
    people_affected = Column(Integer, default=0)
    people_injured = Column(Integer, default=0)

    # Costos estimados
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Departamento donde ocurrió
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    resources = relationship("EmergencyResource", back_populates="emergency", cascade="all, delete-orphan")
    files = relationship("EmergencyFile", back_populates="emergency", cascade="all, delete-orphan")


class EmergencyResource(Base):
    """
    Recursos utilizados en una emergencia.
    """
    __tablename__ = "emergency_resources"

    id = Column(Integer, primary_key=True, index=True)

    # Emergencia
    emergency_id = Column(Integer, ForeignKey("emergencies.id"), nullable=False)
    emergency = relationship("Emergency", back_populates="resources")

    # Tipo de recurso
    resource_type = Column(String(100), nullable=False)  # Ambulancia, SCBA, Personal, etc.
    resource_name = Column(String(255), nullable=False)

    # Equipo utilizado (si aplica)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)

    # Personal asignado (si aplica)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Cantidad
    quantity = Column(Integer, default=1)

    # Notas
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmergencyFile(Base):
    """
    Archivos adjuntos a una emergencia.
    """
    __tablename__ = "emergency_files"

    id = Column(Integer, primary_key=True, index=True)

    # Emergencia
    emergency_id = Column(Integer, ForeignKey("emergencies.id"), nullable=False)
    emergency = relationship("Emergency", back_populates="files")

    # Información del archivo
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_url = Column(String(500), nullable=False)

    # Descripción
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
