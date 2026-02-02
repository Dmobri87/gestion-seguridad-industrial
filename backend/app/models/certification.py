from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class CertificationStatus(str, enum.Enum):
    """Estados de certificación"""
    ACTIVE = "Vigente"
    EXPIRING_SOON = "Por Vencer"
    EXPIRED = "Vencido"
    PENDING = "Pendiente"


class AlertPriority(str, enum.Enum):
    """Prioridad de alerta"""
    INFO = "Informativa"  # 30 días
    WARNING = "Advertencia"  # 15 días
    URGENT = "Urgente"  # 7 días
    CRITICAL = "Crítica"  # Vencido


class CertificationType(Base):
    """
    Tipos de certificaciones.
    Ej: Trabajo en Altura, Conducción de Ambulancia, SOAT, etc.
    """
    __tablename__ = "certification_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Tipo: Personal o Vehículo
    applies_to = Column(String(50), nullable=False)  # 'personal' o 'vehicle'

    # Duración por defecto (en días)
    default_validity_days = Column(Integer, default=365)

    # Días de anticipación para alertas
    alert_days_30 = Column(Boolean, default=True)  # Alerta a 30 días
    alert_days_15 = Column(Boolean, default=True)  # Alerta a 15 días
    alert_days_7 = Column(Boolean, default=True)   # Alerta a 7 días

    # Configuración
    is_mandatory = Column(Boolean, default=True)  # Es obligatoria
    blocks_on_expiry = Column(Boolean, default=True)  # Bloquea al vencer

    # Icono y color para UI
    icon = Column(String(50), nullable=True)
    color = Column(String(20), default="#1890ff")

    # Orden de visualización
    display_order = Column(Integer, default=0)

    # Estado
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    user_certifications = relationship("UserCertification", back_populates="certification_type")
    vehicle_documents = relationship("VehicleDocument", back_populates="document_type")


class UserCertification(Base):
    """
    Certificaciones de personal.
    """
    __tablename__ = "user_certifications"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="certifications")

    # Tipo de certificación
    certification_type_id = Column(Integer, ForeignKey("certification_types.id"), nullable=False)
    certification_type = relationship("CertificationType", back_populates="user_certifications")

    # Número de certificado/documento
    certificate_number = Column(String(100), nullable=True)

    # Entidad emisora
    issuing_entity = Column(String(255), nullable=True)

    # Fechas
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)

    # Estado calculado
    status = Column(String(50), default=CertificationStatus.ACTIVE.value)

    # Archivo adjunto
    file_url = Column(String(500), nullable=True)

    # Notas
    notes = Column(Text, nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    alerts = relationship("CertificationAlert", back_populates="user_certification", cascade="all, delete-orphan")


class VehicleDocument(Base):
    """
    Documentos de vehículos (SOAT, Revisión Técnico-Mecánica, etc.)
    """
    __tablename__ = "vehicle_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Equipo (vehículo)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)

    # Tipo de documento
    document_type_id = Column(Integer, ForeignKey("certification_types.id"), nullable=False)
    document_type = relationship("CertificationType", back_populates="vehicle_documents")

    # Número de documento
    document_number = Column(String(100), nullable=True)

    # Entidad emisora
    issuing_entity = Column(String(255), nullable=True)

    # Fechas
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)

    # Estado calculado
    status = Column(String(50), default=CertificationStatus.ACTIVE.value)

    # Archivo adjunto
    file_url = Column(String(500), nullable=True)

    # Costo
    cost = Column(Integer, nullable=True)

    # Notas
    notes = Column(Text, nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    alerts = relationship("CertificationAlert", back_populates="vehicle_document", cascade="all, delete-orphan")


class CertificationAlert(Base):
    """
    Alertas de vencimiento de certificaciones.
    """
    __tablename__ = "certification_alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Puede ser de personal o vehículo
    user_certification_id = Column(Integer, ForeignKey("user_certifications.id"), nullable=True)
    user_certification = relationship("UserCertification", back_populates="alerts")

    vehicle_document_id = Column(Integer, ForeignKey("vehicle_documents.id"), nullable=True)
    vehicle_document = relationship("VehicleDocument", back_populates="alerts")

    # Tipo de alerta
    alert_type = Column(String(50), nullable=False)  # 30_days, 15_days, 7_days, expired
    priority = Column(String(50), default=AlertPriority.INFO.value)

    # Mensaje
    message = Column(Text, nullable=False)

    # Estado
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    # Usuario notificado
    notified_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Fecha de envío de email
    email_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    """
    Notificaciones generales del sistema.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario destinatario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Tipo de notificación
    notification_type = Column(String(100), nullable=False)  # certification_alert, plan_assigned, etc.

    # Título y mensaje
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Enlace relacionado
    link = Column(String(500), nullable=True)

    # Prioridad
    priority = Column(String(50), default="normal")  # low, normal, high, urgent

    # Estado
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationSetting(Base):
    """
    Preferencias de notificaciones por usuario.
    """
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Preferencias de email
    email_certification_alerts = Column(Boolean, default=True)
    email_plan_assignments = Column(Boolean, default=True)
    email_emergency_alerts = Column(Boolean, default=True)
    email_weekly_summary = Column(Boolean, default=True)

    # Preferencias in-app
    push_certification_alerts = Column(Boolean, default=True)
    push_plan_assignments = Column(Boolean, default=True)
    push_emergency_alerts = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
