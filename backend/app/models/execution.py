from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ExecutionStatus(str, enum.Enum):
    """Estados de ejecución"""
    COMPLETED = "Completado"
    PENDING = "Pendiente"
    WITH_NOVELTY = "Con Novedad"
    CANCELLED = "Cancelado"


class ApprovalStatus(str, enum.Enum):
    """Estados de aprobación"""
    PENDING = "Pendiente"
    APPROVED = "Aprobado"
    REJECTED = "Rechazado"


class ActivityExecution(Base):
    """
    Registro de ejecución de actividades.
    Cada vez que un TAE completa una actividad, se registra aquí.
    """
    __tablename__ = "activity_executions"

    id = Column(Integer, primary_key=True, index=True)

    # Actividad planeada
    planned_activity_id = Column(Integer, ForeignKey("planned_activities.id"), nullable=False)
    planned_activity = relationship("PlannedActivity", back_populates="executions")

    # Usuario que ejecutó
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="executions", foreign_keys=[user_id])

    # Fecha de ejecución
    execution_date = Column(Date, nullable=False)
    execution_time = Column(DateTime(timezone=True), server_default=func.now())

    # Ciclo al que pertenece (1-4)
    cycle_number = Column(Integer, nullable=False)

    # Estado de la ejecución
    status = Column(String(50), default=ExecutionStatus.COMPLETED.value)

    # Observaciones/notas
    observation = Column(Text, nullable=True)
    novelty_description = Column(Text, nullable=True)  # Si tiene novedad

    # Ubicación (opcional)
    location = Column(String(255), nullable=True)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

    # Cantidad ejecutada (para actividades que se miden en cantidad)
    quantity = Column(Integer, default=1)

    # Aprobación
    approval_status = Column(String(50), default=ApprovalStatus.PENDING.value)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Edición
    is_editable = Column(Boolean, default=True)
    edit_deadline = Column(DateTime(timezone=True), nullable=True)  # 24 horas después
    edited_at = Column(DateTime(timezone=True), nullable=True)
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    files = relationship("ExecutionFile", back_populates="execution", cascade="all, delete-orphan")
    history = relationship("ExecutionHistory", back_populates="execution", cascade="all, delete-orphan")


class ExecutionFile(Base):
    """
    Archivos adjuntos a una ejecución (evidencias).
    Fotos, PDFs, videos, etc.
    """
    __tablename__ = "execution_files"

    id = Column(Integer, primary_key=True, index=True)

    # Ejecución
    execution_id = Column(Integer, ForeignKey("activity_executions.id"), nullable=False)
    execution = relationship("ActivityExecution", back_populates="files")

    # Información del archivo
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)  # image/jpeg, application/pdf, etc.
    file_size = Column(Integer, nullable=True)  # En bytes
    file_url = Column(String(500), nullable=False)  # URL en storage (MinIO/S3)

    # Descripción
    description = Column(Text, nullable=True)

    # Metadatos
    is_primary = Column(Boolean, default=False)  # Archivo principal

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)


class ExecutionHistory(Base):
    """
    Historial de cambios en las ejecuciones (auditoría).
    """
    __tablename__ = "execution_history"

    id = Column(Integer, primary_key=True, index=True)

    # Ejecución
    execution_id = Column(Integer, ForeignKey("activity_executions.id"), nullable=False)
    execution = relationship("ActivityExecution", back_populates="history")

    # Tipo de acción
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, APPROVE, REJECT

    # Cambios
    field_changed = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Usuario que realizó el cambio
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Razón del cambio
    reason = Column(Text, nullable=True)

    # Timestamp
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
