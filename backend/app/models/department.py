from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Department(Base):
    """
    Modelo para departamentos/áreas dentro de una organización.
    Ej: CAE Norte, CAE Sur, Área de Seguridad, etc.
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False)  # Código interno
    description = Column(Text, nullable=True)

    # Relación con organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="departments")

    # Jerarquía (departamento padre)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    parent = relationship("Department", remote_side=[id], backref="subdepartments")

    # Estado
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    users = relationship("User", back_populates="department")
