from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List


class OrganizationBase(BaseModel):
    """Schema base para organización."""
    name: str
    code: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = "#1890ff"


class OrganizationCreate(OrganizationBase):
    """Schema para crear organización."""
    max_users: Optional[int] = 100


class OrganizationUpdate(BaseModel):
    """Schema para actualizar organización."""
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    is_active: Optional[bool] = None
    max_users: Optional[int] = None


class OrganizationResponse(OrganizationBase):
    """Schema de respuesta para organización."""
    id: int
    is_active: bool
    max_users: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DEPARTAMENTOS
# ==========================================

class DepartmentBase(BaseModel):
    """Schema base para departamento."""
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    """Schema para crear departamento."""
    organization_id: int


class DepartmentUpdate(BaseModel):
    """Schema para actualizar departamento."""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Schema de respuesta para departamento."""
    id: int
    organization_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentWithUsers(DepartmentResponse):
    """Departamento con lista de usuarios."""
    users_count: int = 0
