from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    program_id = Column(Integer, ForeignKey("programs.id"))