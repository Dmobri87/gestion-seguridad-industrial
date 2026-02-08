from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # ✅ ForeignKey agregado correctamente
    coordinator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relación opcional para acceder al coordinador
    coordinator = relationship("User", backref="coordinated_programs")