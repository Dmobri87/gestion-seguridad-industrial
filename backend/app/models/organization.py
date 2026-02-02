from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Organization(Base):
    """
    Modelo para organizaciones (multi-tenant).
    Cada empresa minera/industrial es una organización.
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # Código único
    description = Column(Text, nullable=True)

    # Datos de contacto
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    # Logo y branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(20), default="#1890ff")  # Hex color

    # Estado
    is_active = Column(Boolean, default=True)

    # Configuración
    max_users = Column(Integer, default=100)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")
