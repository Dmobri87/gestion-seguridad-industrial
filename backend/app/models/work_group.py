from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class WorkGroup(Base):
    """
    Grupos de trabajo (Valientes, Guerreros, Jaguares, etc.)
    Cada grupo tiene un Coordinador y varios TAEs/PSEs.
    """
    __tablename__ = "work_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(20), default="#1890ff")

    # Coordinador del grupo
    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    coordinator = relationship("User", foreign_keys=[coordinator_id], backref="coordinated_group")

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization")

    # Estado
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con usuarios del grupo
    members = relationship("User", back_populates="work_group", foreign_keys="User.work_group_id")
