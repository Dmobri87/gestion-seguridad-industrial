from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "Administrador"
    COORDINATOR = "Coordinador"
    SUPERVISOR = "Supervisor"
    TAE = "TAE"  # Técnico de Atención de Emergencias
    PSE = "PSE"  # Personal de Soporte a Emergencias
    EMPLOYEE = "Empleado"
    GUEST = "Invitado"


class User(Base):
    """
    Modelo de usuario mejorado con soporte multi-tenant.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Datos de autenticación
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Datos personales
    full_name = Column(String(255), nullable=False)
    employee_code = Column(String(50), nullable=True, index=True)  # Código de empleado
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Rol y permisos
    role = Column(String(50), default=UserRole.EMPLOYEE.value)

    # Relación con organización (multi-tenant)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="users")

    # Relación con departamento
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department = relationship("Department", back_populates="users")

    # Grupo de trabajo
    work_group_id = Column(Integer, ForeignKey("work_groups.id"), nullable=True)
    work_group = relationship("WorkGroup", back_populates="members", foreign_keys=[work_group_id])

    # Supervisor directo
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    supervisor = relationship("User", remote_side=[id], backref="subordinates")

    # Estado
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 2FA
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)

    # OTP para autenticación de dos factores por email
    otp_code = Column(String(64), nullable=True)  # Hash SHA256 del OTP
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    otp_attempts = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    monthly_plans = relationship("MonthlyPlan", back_populates="user", foreign_keys="MonthlyPlan.user_id")
    created_plans = relationship("MonthlyPlan", back_populates="created_by_user", foreign_keys="MonthlyPlan.created_by")
    executions = relationship("ActivityExecution", back_populates="user", foreign_keys="ActivityExecution.user_id")
    certifications = relationship("UserCertification", back_populates="user")
