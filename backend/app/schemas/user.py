from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


# Roles del sistema (mantener compatibilidad con el modelo existente)
class UserRoleEnum(str, Enum):
    ADMIN = "Administrador"
    COORDINATOR = "Coordinador"
    SUPERVISOR = "Supervisor"
    TAE = "TAE"
    PSE = "PSE"
    EMPLOYEE = "Empleado"
    GUEST = "Invitado"


# ==========================================
# SCHEMAS LEGACY (mantener compatibilidad)
# ==========================================

class UserRole(str, Enum):
    ADMIN = "Administrador"
    SUPERVISOR = "Supervisor"
    COORDINADOR = "Coordinador"
    EMPLEADO = "Empleado"


class UserCreate(BaseModel):
    """Schema para crear usuario (compatible con versión anterior)."""
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.EMPLEADO
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    supervisor_id: Optional[int] = None

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        return _validate_password_strength(v)


class UserOut(BaseModel):
    """Schema de salida (compatible con versión anterior)."""
    id: int
    email: EmailStr
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True


# ==========================================
# SCHEMAS NUEVOS (API v1)
# ==========================================

VALID_ROLES = {"Administrador", "Coordinador", "Supervisor", "TAE", "PSE", "Paramédico", "Empleado", "Invitado"}


def _validate_password_strength(v: str) -> str:
    """Validación centralizada de fortaleza de contraseña."""
    if len(v) < 8:
        raise ValueError('La contraseña debe tener al menos 8 caracteres')
    if len(v) > 128:
        raise ValueError('La contraseña no puede exceder 128 caracteres')
    if not any(c.isupper() for c in v):
        raise ValueError('La contraseña debe contener al menos una letra mayúscula')
    if not any(c.islower() for c in v):
        raise ValueError('La contraseña debe contener al menos una letra minúscula')
    if not any(c.isdigit() for c in v):
        raise ValueError('La contraseña debe contener al menos un número')
    return v


class UserBase(BaseModel):
    """Schema base para usuario."""
    email: EmailStr
    full_name: str
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    role: str = "Empleado"

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in VALID_ROLES:
            raise ValueError(f'Rol no válido. Roles permitidos: {", ".join(sorted(VALID_ROLES))}')
        return v


class UserCreateV1(UserBase):
    """Schema para crear usuario (API v1)."""
    password: str
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    work_group_id: Optional[int] = None
    supervisor_id: Optional[int] = None

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        return _validate_password_strength(v)


class UserUpdate(BaseModel):
    """Schema para actualizar usuario."""
    full_name: Optional[str] = None
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[int] = None
    work_group_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema de respuesta para usuario."""
    id: int
    avatar_url: Optional[str] = None
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    work_group_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserWithDetails(UserResponse):
    """Usuario con detalles de organización y departamento."""
    organization_name: Optional[str] = None
    department_name: Optional[str] = None
    work_group_name: Optional[str] = None
    supervisor_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema para login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema para token JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Datos contenidos en el token."""
    user_id: int
    email: str
    role: str
    organization_id: Optional[int] = None


class ProfileUpdate(BaseModel):
    """Schema para que el usuario actualice su propio perfil."""
    full_name: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema para cambio de contraseña."""
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        return _validate_password_strength(v)


class PasswordReset(BaseModel):
    """Schema para reset de contraseña."""
    email: EmailStr


# ==========================================
# SCHEMAS 2FA / OTP
# ==========================================

class OTPVerifyRequest(BaseModel):
    """Schema para verificacion de codigo OTP."""
    email: EmailStr
    otp_code: str

    @field_validator('otp_code')
    @classmethod
    def validate_otp_code(cls, v):
        if not v or len(v) != 8 or not v.isdigit():
            raise ValueError('El codigo OTP debe ser de 8 digitos')
        return v


class LoginOTPResponse(BaseModel):
    """Respuesta cuando se requiere verificación 2FA."""
    requires_2fa: bool = True
    message: str
    dev_otp: Optional[str] = None
