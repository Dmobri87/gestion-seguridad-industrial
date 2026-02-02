from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ActivityCategory(Base):
    """
    Categorías de actividades (las 8 del Excel).
    Ej: IMPLEMENTACIÓN INTERNA SIO, SISTEMA DE EMERGENCIAS, etc.
    """
    __tablename__ = "activity_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, unique=True)  # SIO, EMERGENCIAS, etc.
    description = Column(Text, nullable=True)

    # Orden de visualización
    display_order = Column(Integer, default=0)

    # Color para UI
    color = Column(String(20), default="#1890ff")  # Hex color
    icon = Column(String(50), nullable=True)  # Nombre del icono

    # Estado
    is_active = Column(Boolean, default=True)

    # Organización (si es específica de una org, null = global)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    activity_templates = relationship("ActivityTemplate", back_populates="category")


class ActivityTemplate(Base):
    """
    Plantillas de actividades predefinidas (las 93 del Excel).
    Son las actividades base que se asignan en los planes mensuales.
    """
    __tablename__ = "activity_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Categoría
    category_id = Column(Integer, ForeignKey("activity_categories.id"), nullable=False)
    category = relationship("ActivityCategory", back_populates="activity_templates")

    # Código interno
    code = Column(String(50), nullable=True, index=True)

    # Orden dentro de la categoría
    display_order = Column(Integer, default=0)

    # Configuración
    requires_evidence = Column(Boolean, default=False)  # Requiere foto/documento
    is_critical = Column(Boolean, default=False)  # Actividad crítica
    default_frequency = Column(Integer, default=1)  # Frecuencia sugerida por ciclo

    # Estado
    is_active = Column(Boolean, default=True)

    # Organización (si es específica de una org, null = global)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    planned_activities = relationship("PlannedActivity", back_populates="activity_template")
