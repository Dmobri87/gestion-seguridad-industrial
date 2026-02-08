from pydantic import BaseModel
from datetime import datetime
from typing import List

class AssignmentCreate(BaseModel):
    """Schema para asignar una actividad a uno o más usuarios"""
    activity_id: int
    user_ids: List[int]  # Lista de IDs de usuarios a asignar


class AssignmentOut(BaseModel):
    """Schema para devolver información de una asignación"""
    id: int
    activity_id: int
    user_id: int
    assigned_date: datetime
    assigned_by: int

    class Config:
        from_attributes = True


class AssignmentDetail(BaseModel):
    """Schema con información detallada de la asignación"""
    id: int
    activity_id: int
    activity_name: str
    user_id: int
    user_name: str
    user_email: str
    assigned_date: datetime
    assigned_by: int
    assigned_by_name: str