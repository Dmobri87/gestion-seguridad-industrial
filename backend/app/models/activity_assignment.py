from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class ActivityAssignment(Base):
    """
    Tabla que registra qué actividades están asignadas a qué usuarios.
    
    Una actividad puede estar asignada a múltiples usuarios.
    Un usuario puede tener múltiples actividades asignadas.
    """
    __tablename__ = "activity_assignments"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_date = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Quién asignó