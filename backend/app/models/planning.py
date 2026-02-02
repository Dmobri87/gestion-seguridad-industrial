from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Float, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class PlanStatus(str, enum.Enum):
    """Estados del plan mensual"""
    DRAFT = "Borrador"
    APPROVED = "Aprobado"
    IN_PROGRESS = "En Progreso"
    COMPLETED = "Completado"
    CANCELLED = "Cancelado"


class MonthlyPlan(Base):
    """
    Plan mensual de actividades para un TAE.
    Un usuario solo puede tener UN plan por mes.
    """
    __tablename__ = "monthly_plans"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario asignado (TAE)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="monthly_plans", foreign_keys=[user_id])

    # Período
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Estado del plan
    status = Column(String(50), default=PlanStatus.DRAFT.value)

    # Observaciones
    notes = Column(Text, nullable=True)

    # Creado por (Coordinador)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User", back_populates="created_plans", foreign_keys=[created_by])

    # Aprobado por
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Organización
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Métricas calculadas
    total_planned = Column(Integer, default=0)
    total_executed = Column(Integer, default=0)
    compliance_percentage = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    cycles = relationship("PlanningCycle", back_populates="monthly_plan", cascade="all, delete-orphan")
    planned_activities = relationship("PlannedActivity", back_populates="monthly_plan", cascade="all, delete-orphan")

    # Constraint: un usuario solo puede tener un plan por mes
    __table_args__ = (
        UniqueConstraint('user_id', 'year', 'month', name='uq_user_year_month'),
    )


class PlanningCycle(Base):
    """
    Ciclos semanales dentro del plan mensual.
    Típicamente 4 ciclos por mes.
    """
    __tablename__ = "planning_cycles"

    id = Column(Integer, primary_key=True, index=True)

    # Plan mensual
    monthly_plan_id = Column(Integer, ForeignKey("monthly_plans.id"), nullable=False)
    monthly_plan = relationship("MonthlyPlan", back_populates="cycles")

    # Número de ciclo (1-4)
    cycle_number = Column(Integer, nullable=False)

    # Fechas del ciclo
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Métricas calculadas
    total_planned = Column(Integer, default=0)
    total_executed = Column(Integer, default=0)
    compliance_percentage = Column(Float, default=0.0)

    # Estado
    is_current = Column(Boolean, default=False)  # Es el ciclo actual?

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PlannedActivity(Base):
    """
    Actividades planeadas dentro de un plan mensual.
    Define cuántas veces se debe ejecutar cada actividad por ciclo.
    """
    __tablename__ = "planned_activities"

    id = Column(Integer, primary_key=True, index=True)

    # Plan mensual
    monthly_plan_id = Column(Integer, ForeignKey("monthly_plans.id"), nullable=False)
    monthly_plan = relationship("MonthlyPlan", back_populates="planned_activities")

    # Plantilla de actividad
    activity_template_id = Column(Integer, ForeignKey("activity_templates.id"), nullable=False)
    activity_template = relationship("ActivityTemplate", back_populates="planned_activities")

    # Cantidad planeada por ciclo
    cycle_1_planned = Column(Integer, default=0)
    cycle_2_planned = Column(Integer, default=0)
    cycle_3_planned = Column(Integer, default=0)
    cycle_4_planned = Column(Integer, default=0)

    # Cantidad ejecutada por ciclo
    cycle_1_executed = Column(Integer, default=0)
    cycle_2_executed = Column(Integer, default=0)
    cycle_3_executed = Column(Integer, default=0)
    cycle_4_executed = Column(Integer, default=0)

    # Totales
    total_planned = Column(Integer, default=0)
    total_executed = Column(Integer, default=0)
    compliance_percentage = Column(Float, default=0.0)

    # Notas específicas
    notes = Column(Text, nullable=True)

    # Estado
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    executions = relationship("ActivityExecution", back_populates="planned_activity")
