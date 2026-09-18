from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, timedelta
import json
import calendar

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.planning import MonthlyPlan, PlanningCycle, PlannedActivity, PlanStatus
from app.models.execution import ActivityExecution
from app.models.activity_category import ActivityTemplate
from app.models.compliance import AuditLog
from app.schemas.planning import (
    MonthlyPlanResponse, MonthlyPlanCreate, MonthlyPlanUpdate, MonthlyPlanWithDetails,
    PlanningCycleResponse,
    PlannedActivityResponse, PlannedActivityCreate, PlannedActivityUpdate, PlannedActivityWithTemplate,
    BulkPlannedActivityCreate, PlanWithActivities,
    BulkMonthlyPlanCreate, BulkCreateResponse
)

router = APIRouter()
PLAN_CYCLES = 3


# ==========================================
# PLANES MENSUALES
# ==========================================

@router.get("/plans", response_model=List[MonthlyPlanWithDetails])
async def get_monthly_plans(
    year: int = Query(..., ge=2020, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar planes mensuales con filtros.
    """
    query = db.query(MonthlyPlan).options(
        joinedload(MonthlyPlan.user),
        joinedload(MonthlyPlan.created_by_user)
    )

    # Filtrar por organización (incluye planes con organization_id NULL por compatibilidad)
    if current_user.organization_id:
        query = query.filter(
            (MonthlyPlan.organization_id == current_user.organization_id) |
            (MonthlyPlan.organization_id.is_(None))
        )

    # Filtros
    query = query.filter(MonthlyPlan.year == year)

    if month:
        query = query.filter(MonthlyPlan.month == month)

    if user_id:
        query = query.filter(MonthlyPlan.user_id == user_id)

    if status:
        query = query.filter(MonthlyPlan.status == status)

    plans = query.order_by(MonthlyPlan.year.desc(), MonthlyPlan.month.desc()).all()

    result = []
    for plan in plans:
        plan_dict = MonthlyPlanWithDetails.model_validate(plan)
        plan_dict.user_name = plan.user.full_name if plan.user else ""
        plan_dict.user_email = plan.user.email if plan.user else ""
        plan_dict.created_by_name = plan.created_by_user.full_name if plan.created_by_user else ""
        result.append(plan_dict)

    return result


@router.get("/plans/{plan_id}", response_model=PlanWithActivities)
async def get_monthly_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener plan mensual completo con todas sus actividades.
    """
    plan = db.query(MonthlyPlan).options(
        joinedload(MonthlyPlan.user),
        joinedload(MonthlyPlan.created_by_user),
        joinedload(MonthlyPlan.cycles),
        joinedload(MonthlyPlan.planned_activities).joinedload(PlannedActivity.activity_template).joinedload(ActivityTemplate.category)
    ).filter(MonthlyPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado"
        )

    # Control de acceso por organización y rol.
    # Admin: acceso total.
    # Coordinador/Supervisor: su misma organización y, si aplica, su grupo de trabajo.
    # Resto de roles: solo su propio plan.
    plan_org_id = plan.organization_id or (plan.user.organization_id if plan.user else None)
    if (
        current_user.organization_id
        and plan_org_id
        and plan_org_id != current_user.organization_id
        and current_user.role != UserRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este plan"
        )

    if current_user.role != UserRole.ADMIN.value:
        if current_user.role in {UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value}:
            if (
                current_user.work_group_id
                and plan.user
                and plan.user.work_group_id != current_user.work_group_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes acceso a planes fuera de tu grupo de trabajo"
                )
        elif plan.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a este plan"
            )

    # Construir respuesta con actividades detalladas
    planned_activities = []
    for pa in plan.planned_activities:
        if pa.activity_template:
            pa_dict = {
                **PlannedActivityResponse.model_validate(pa).model_dump(),
                "activity_name": pa.activity_template.name,
                "activity_code": pa.activity_template.code or "",
                "category_id": pa.activity_template.category_id,
                "category_name": pa.activity_template.category.name if pa.activity_template.category else "",
                "category_code": pa.activity_template.category.code if pa.activity_template.category else "",
                "requires_evidence": pa.requires_evidence,
                "is_critical": pa.activity_template.is_critical,
                "coordinator_only": pa.activity_template.coordinator_only
            }
            planned_activities.append(PlannedActivityWithTemplate(**pa_dict))

    cycles = [PlanningCycleResponse.model_validate(c) for c in plan.cycles]

    return {
        **MonthlyPlanResponse.model_validate(plan).model_dump(),
        "user_name": plan.user.full_name if plan.user else "",
        "user_email": plan.user.email if plan.user else "",
        "created_by_name": plan.created_by_user.full_name if plan.created_by_user else "",
        "planned_activities": planned_activities,
        "cycles": cycles
    }


@router.post("/plans", response_model=MonthlyPlanResponse)
async def create_monthly_plan(
    plan_data: MonthlyPlanCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """
    Crear nuevo plan mensual para un TAE.
    Solo Coordinadores y Administradores.
    """
    # Verificar que no exista plan para este usuario/mes
    existing = db.query(MonthlyPlan).filter(
        and_(
            MonthlyPlan.user_id == plan_data.user_id,
            MonthlyPlan.year == plan_data.year,
            MonthlyPlan.month == plan_data.month
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un plan para este usuario en {plan_data.month}/{plan_data.year}"
        )

    target_user = db.get(User, plan_data.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Fix H-5 (corregido): Coordinadores pueden crear su propio plan aunque no tengan grupo asignado
    if current_user.role == UserRole.COORDINATOR.value:
        if target_user.id != current_user.id:  # Creando plan para otro usuario
            if not current_user.work_group_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene grupo de trabajo asignado para gestionar otros usuarios"
                )
            if target_user.work_group_id != current_user.work_group_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para crear planes a usuarios fuera de tu grupo de trabajo."
                )

    # Crear plan
    plan = MonthlyPlan(
        user_id=plan_data.user_id,
        year=plan_data.year,
        month=plan_data.month,
        notes=plan_data.notes,
        status=PlanStatus.DRAFT.value,
        created_by=current_user.id,
        organization_id=plan_data.organization_id or current_user.organization_id or target_user.organization_id
    )

    db.add(plan)
    db.flush()

    # Crear los 3 ciclos semanales
    _create_planning_cycles(db, plan)

    db.commit()
    db.refresh(plan)

    return plan


def _create_planning_cycles(db: Session, plan: MonthlyPlan):
    """Crear los 3 ciclos semanales para un plan mensual."""
    year = plan.year
    month = plan.month

    # Obtener primer y último día del mes
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    # Calcular fechas de cada ciclo (aproximadamente 7 días cada uno)
    total_days = (last_day - first_day).days + 1
    days_per_cycle = total_days // PLAN_CYCLES

    current_date = first_day
    for cycle_num in range(1, PLAN_CYCLES + 1):
        start_date = current_date

        if cycle_num == PLAN_CYCLES:
            # El último ciclo va hasta el final del mes
            end_date = last_day
        else:
            end_date = start_date + timedelta(days=days_per_cycle - 1)

        cycle = PlanningCycle(
            monthly_plan_id=plan.id,
            cycle_number=cycle_num,
            start_date=start_date,
            end_date=end_date,
            is_current=(cycle_num == 1)  # El primer ciclo es el actual
        )
        db.add(cycle)

        current_date = end_date + timedelta(days=1)


def _write_audit_log(
    db: Session,
    *,
    user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[int],
    description: str,
    old_values: Optional[dict] = None
):
    """Guardar evento de auditoría de forma consistente."""
    log = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        old_values=json.dumps(old_values, ensure_ascii=True) if old_values else None,
        organization_id=user.organization_id
    )
    db.add(log)


@router.post("/plans/bulk", response_model=BulkCreateResponse)
async def bulk_create_monthly_plans(
    bulk_data: BulkMonthlyPlanCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """
    Crear planes mensuales en lote para múltiples usuarios y meses.
    Permite programar un trimestre completo para todo el personal de una vez.
    """
    created = 0
    skipped = 0
    plan_ids = []
    details = []

    # Validar que los usuarios existen y están activos
    users = db.query(User).filter(
        User.id.in_(bulk_data.user_ids),
        User.is_active == True
    ).all()
    valid_user_ids = {u.id for u in users}
    user_names = {u.id: u.full_name for u in users}
    user_org_ids = {u.id: u.organization_id for u in users}
    user_roles = {u.id: u.role for u in users}

    # Fix H-5 (corregido): Coordinadores pueden crear su propio plan aunque no tengan grupo asignado
    if current_user.role == UserRole.COORDINATOR.value:
        other_user_ids = [uid for uid in bulk_data.user_ids if uid != current_user.id and uid in valid_user_ids]
        if other_user_ids:
            if not current_user.work_group_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene grupo de trabajo asignado para gestionar otros usuarios"
                )
            allowed_ids = {
                u.id for u in users if u.work_group_id == current_user.work_group_id
            }
            unauthorized = [uid for uid in other_user_ids if uid not in allowed_ids]
            if unauthorized:
                unauthorized_names = [user_names.get(uid, f"ID {uid}") for uid in unauthorized]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No tienes permiso para crear planes a: {', '.join(unauthorized_names)}. Solo puedes gestionar tu grupo de trabajo."
                )

    # Obtener plantillas activas: separar por coordinator_only según rol destino
    all_templates: list = []
    regular_templates: list = []
    if bulk_data.load_activities:
        all_templates = db.query(ActivityTemplate).filter(
            ActivityTemplate.is_active == True
        ).all()
        regular_templates = [t for t in all_templates if not t.coordinator_only]

    for month_data in bulk_data.months:
        for user_id in bulk_data.user_ids:
            if user_id not in valid_user_ids:
                skipped += 1
                details.append(f"Usuario ID {user_id} no encontrado o inactivo")
                continue

            # Verificar si ya existe
            existing = db.query(MonthlyPlan).filter(
                and_(
                    MonthlyPlan.user_id == user_id,
                    MonthlyPlan.year == month_data.year,
                    MonthlyPlan.month == month_data.month
                )
            ).first()

            if existing:
                skipped += 1
                details.append(
                    f"{user_names.get(user_id, '')} - {month_data.month}/{month_data.year}: ya existe"
                )
                continue

            # Crear plan
            plan = MonthlyPlan(
                user_id=user_id,
                year=month_data.year,
                month=month_data.month,
                notes=bulk_data.notes,
                status=PlanStatus.DRAFT.value,
                created_by=current_user.id,
                organization_id=bulk_data.organization_id or current_user.organization_id or user_org_ids.get(user_id)
            )
            db.add(plan)
            db.flush()

            # Crear los 3 ciclos semanales
            _create_planning_cycles(db, plan)

            # Cargar actividades del catálogo según rol del usuario destino
            if bulk_data.load_activities and all_templates:
                COORDINATOR_ROLES = {"Administrador", "Coordinador", "Supervisor"}
                target_role = user_roles.get(user_id, "")
                templates_for_user = all_templates if target_role in COORDINATOR_ROLES else regular_templates
                total_plan = 0
                for tmpl in templates_for_user:
                    freq = tmpl.default_frequency or 1
                    total_act = freq * PLAN_CYCLES
                    pa = PlannedActivity(
                        monthly_plan_id=plan.id,
                        activity_template_id=tmpl.id,
                        cycle_1_planned=freq,
                        cycle_2_planned=freq,
                        cycle_3_planned=freq,
                        cycle_4_planned=0,
                        requires_evidence=True,
                        total_planned=total_act,
                    )
                    db.add(pa)
                    total_plan += total_act
                plan.total_planned = total_plan

            plan_ids.append(plan.id)
            created += 1

    db.commit()

    return BulkCreateResponse(
        created=created,
        skipped=skipped,
        plan_ids=plan_ids,
        details=details
    )


@router.put("/plans/{plan_id}", response_model=MonthlyPlanResponse)
async def update_monthly_plan(
    plan_id: int,
    plan_data: MonthlyPlanUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """
    Actualizar plan mensual (estado, notas).
    """
    plan = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado"
        )

    # Fix H-2: Organization scoping check
    if plan.organization_id and current_user.organization_id and plan.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)

    return plan


@router.delete("/plans/{plan_id}")
async def delete_monthly_plan(
    plan_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Eliminar plan mensual completo (solo Administrador).
    Bloquea eliminación si existen ejecuciones asociadas.
    """
    plan = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado"
        )

    if current_user.organization_id and plan.organization_id and plan.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes eliminar planes de otra organización"
        )

    executions_count = db.query(ActivityExecution.id).join(
        PlannedActivity, PlannedActivity.id == ActivityExecution.planned_activity_id
    ).filter(
        PlannedActivity.monthly_plan_id == plan_id
    ).count()

    if executions_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el plan porque ya tiene ejecuciones registradas"
        )

    plan_snapshot = {
        "id": plan.id,
        "user_id": plan.user_id,
        "user_name": plan.user.full_name if plan.user else None,
        "year": plan.year,
        "month": plan.month,
        "status": plan.status,
        "total_planned": plan.total_planned,
        "total_executed": plan.total_executed,
    }
    _write_audit_log(
        db,
        user=current_user,
        action="DELETE",
        resource_type="monthly_plan",
        resource_id=plan.id,
        description=f"Eliminó plan mensual #{plan.id} ({plan.month}/{plan.year}) de {plan.user.full_name if plan.user else f'usuario {plan.user_id}'}",
        old_values=plan_snapshot
    )

    db.delete(plan)
    db.commit()

    return {"message": "Plan eliminado correctamente"}


@router.post("/plans/{plan_id}/approve")
async def approve_monthly_plan(
    plan_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """
    Aprobar un plan mensual.
    """
    from datetime import datetime

    plan = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado"
        )

    # Fix H-2: Organization scoping check
    if plan.organization_id and current_user.organization_id and plan.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    if plan.status != PlanStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden aprobar planes en estado Borrador"
        )

    plan.status = PlanStatus.APPROVED.value
    plan.approved_by = current_user.id
    plan.approved_at = datetime.utcnow()

    db.commit()

    return {"message": "Plan aprobado correctamente"}


# ==========================================
# ACTIVIDADES PLANEADAS
# ==========================================

@router.post("/plans/{plan_id}/activities", response_model=PlannedActivityResponse)
async def add_planned_activity(
    plan_id: int,
    activity_data: PlannedActivityCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """
    Agregar actividad al plan mensual.
    """
    plan = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado"
        )

    # Fix H-2: Organization scoping check
    if plan.organization_id and current_user.organization_id and plan.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Verificar que la plantilla existe
    template = db.query(ActivityTemplate).filter(
        ActivityTemplate.id == activity_data.activity_template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla de actividad no encontrada"
        )

    # Bloquear actividades de coordinador para roles no autorizados
    COORDINATOR_ROLES = {"Administrador", "Coordinador", "Supervisor"}
    if template.coordinator_only and current_user.role not in COORDINATOR_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta actividad es exclusiva de Coordinadores. Solo puede ser asignada manualmente por un Coordinador."
        )

    # Calcular totales
    total_planned = (
        activity_data.cycle_1_planned +
        activity_data.cycle_2_planned +
        activity_data.cycle_3_planned
    )

    planned_activity = PlannedActivity(
        monthly_plan_id=plan_id,
        activity_template_id=activity_data.activity_template_id,
        cycle_1_planned=activity_data.cycle_1_planned,
        cycle_2_planned=activity_data.cycle_2_planned,
        cycle_3_planned=activity_data.cycle_3_planned,
        cycle_4_planned=0,
        requires_evidence=activity_data.requires_evidence,
        total_planned=total_planned,
        notes=activity_data.notes
    )

    db.add(planned_activity)

    # Actualizar total del plan
    plan.total_planned += total_planned
    _recalculate_plan_compliance(plan)

    db.commit()
    db.refresh(planned_activity)

    return planned_activity


@router.post("/plans/{plan_id}/activities/bulk", response_model=List[PlannedActivityResponse])
async def bulk_add_planned_activities(
    plan_id: int,
    bulk_data: BulkPlannedActivityCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """
    Agregar múltiples actividades al plan mensual.
    Útil para crear plan completo de una vez.
    """
    plan = db.query(MonthlyPlan).filter(MonthlyPlan.id == plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan no encontrado"
        )

    created_activities = []

    COORDINATOR_ROLES = {"Administrador", "Coordinador", "Supervisor"}
    template_cache = {t.id: t for t in db.query(ActivityTemplate).filter(
        ActivityTemplate.id.in_([a.activity_template_id for a in bulk_data.activities])
    ).all()}

    for activity_data in bulk_data.activities:
        # Saltar actividades de coordinador si el usuario no tiene rol adecuado
        tmpl = template_cache.get(activity_data.activity_template_id)
        if tmpl and tmpl.coordinator_only and current_user.role not in COORDINATOR_ROLES:
            continue

        total_planned = (
            activity_data.cycle_1_planned +
            activity_data.cycle_2_planned +
            activity_data.cycle_3_planned
        )

        if total_planned > 0:  # Solo agregar si hay algo planeado
            planned_activity = PlannedActivity(
                monthly_plan_id=plan_id,
                activity_template_id=activity_data.activity_template_id,
                cycle_1_planned=activity_data.cycle_1_planned,
                cycle_2_planned=activity_data.cycle_2_planned,
                cycle_3_planned=activity_data.cycle_3_planned,
                cycle_4_planned=0,
                requires_evidence=activity_data.requires_evidence,
                total_planned=total_planned,
                notes=activity_data.notes
            )
            db.add(planned_activity)
            created_activities.append(planned_activity)

            plan.total_planned += total_planned

    _recalculate_plan_compliance(plan)

    db.commit()

    for activity in created_activities:
        db.refresh(activity)

    return created_activities


@router.put("/activities/{activity_id}", response_model=PlannedActivityResponse)
async def update_planned_activity(
    activity_id: int,
    activity_data: PlannedActivityUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """
    Actualizar actividad planeada.
    """
    activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )

    # Fix H-2: Organization scoping check via the parent plan
    plan = activity.monthly_plan
    if plan and plan.organization_id and current_user.organization_id and plan.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Guardar totales anteriores
    old_total = activity.total_planned

    # Actualizar campos
    update_data = activity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)

    # Planificación opera con 3 ciclos; el cuarto se mantiene en 0 por compatibilidad de esquema.
    activity.cycle_4_planned = 0

    # Recalcular total
    activity.total_planned = (
        activity.cycle_1_planned +
        activity.cycle_2_planned +
        activity.cycle_3_planned
    )

    # Recalcular compliance de la actividad
    if activity.total_planned > 0:
        activity.compliance_percentage = (activity.total_executed / activity.total_planned) * 100
    else:
        activity.compliance_percentage = 0

    # Actualizar plan
    plan.total_planned = plan.total_planned - old_total + activity.total_planned
    _recalculate_plan_compliance(plan)

    db.commit()
    db.refresh(activity)

    return activity


@router.delete("/activities/{activity_id}")
async def delete_planned_activity(
    activity_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Eliminar actividad planeada (solo Administrador).
    Bloquea eliminación si ya tiene ejecuciones.
    """
    activity = db.query(PlannedActivity).filter(PlannedActivity.id == activity_id).first()

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )

    plan = activity.monthly_plan
    if current_user.organization_id and plan.organization_id and plan.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes eliminar actividades de otra organización"
        )

    executions_count = db.query(ActivityExecution.id).filter(
        ActivityExecution.planned_activity_id == activity_id
    ).count()

    if executions_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la actividad porque ya tiene ejecuciones registradas"
        )

    activity_snapshot = {
        "id": activity.id,
        "monthly_plan_id": activity.monthly_plan_id,
        "activity_template_id": activity.activity_template_id,
        "activity_name": activity.activity_template.name if activity.activity_template else None,
        "total_planned": activity.total_planned,
        "total_executed": activity.total_executed,
    }
    _write_audit_log(
        db,
        user=current_user,
        action="DELETE",
        resource_type="planned_activity",
        resource_id=activity.id,
        description=f"Eliminó actividad planeada #{activity.id} del plan #{activity.monthly_plan_id}",
        old_values=activity_snapshot
    )

    plan.total_planned = max(0, plan.total_planned - activity.total_planned)
    plan.total_executed = max(0, plan.total_executed - activity.total_executed)
    _recalculate_plan_compliance(plan)

    db.delete(activity)
    db.commit()

    return {"message": "Actividad eliminada correctamente"}


@router.get("/audit/deletions")
async def get_deletion_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Obtener historial de auditoría de eliminaciones en planificación (solo Admin).
    """
    query = db.query(AuditLog).filter(
        AuditLog.action == "DELETE",
        AuditLog.resource_type.in_(["monthly_plan", "planned_activity"])
    )

    if current_user.organization_id:
        query = query.filter(AuditLog.organization_id == current_user.organization_id)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "user_email": log.user_email,
            "created_at": log.created_at,
        })
    return result


def _recalculate_plan_compliance(plan: MonthlyPlan):
    """Recalcular el porcentaje de cumplimiento del plan."""
    if plan.total_planned > 0:
        plan.compliance_percentage = (plan.total_executed / plan.total_planned) * 100
    else:
        plan.compliance_percentage = 0


# ==========================================
# PLAN DEL USUARIO ACTUAL
# ==========================================

@router.get("/my-plan", response_model=PlanWithActivities)
async def get_my_current_plan(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener el plan del usuario actual para un mes específico.
    """
    plan = db.query(MonthlyPlan).options(
        joinedload(MonthlyPlan.cycles),
        joinedload(MonthlyPlan.planned_activities).joinedload(PlannedActivity.activity_template).joinedload(ActivityTemplate.category)
    ).filter(
        and_(
            MonthlyPlan.user_id == current_user.id,
            MonthlyPlan.year == year,
            MonthlyPlan.month == month
        )
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes plan asignado para este mes"
        )

    # Construir respuesta
    planned_activities = []
    for pa in plan.planned_activities:
        if pa.activity_template:
            pa_dict = {
                **PlannedActivityResponse.model_validate(pa).model_dump(),
                "activity_name": pa.activity_template.name,
                "activity_code": pa.activity_template.code or "",
                "category_id": pa.activity_template.category_id,
                "category_name": pa.activity_template.category.name if pa.activity_template.category else "",
                "category_code": pa.activity_template.category.code if pa.activity_template.category else "",
                "requires_evidence": pa.requires_evidence,
                "is_critical": pa.activity_template.is_critical,
                "coordinator_only": pa.activity_template.coordinator_only
            }
            planned_activities.append(PlannedActivityWithTemplate(**pa_dict))

    cycles = [PlanningCycleResponse.model_validate(c) for c in plan.cycles]

    return {
        **MonthlyPlanResponse.model_validate(plan).model_dump(),
        "user_name": current_user.full_name,
        "user_email": current_user.email,
        "created_by_name": "",
        "planned_activities": planned_activities,
        "cycles": cycles
    }
