from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, timedelta
import calendar

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.planning import MonthlyPlan, PlanningCycle, PlannedActivity, PlanStatus
from app.models.activity_category import ActivityTemplate
from app.schemas.planning import (
    MonthlyPlanResponse, MonthlyPlanCreate, MonthlyPlanUpdate, MonthlyPlanWithDetails,
    PlanningCycleResponse,
    PlannedActivityResponse, PlannedActivityCreate, PlannedActivityUpdate, PlannedActivityWithTemplate,
    BulkPlannedActivityCreate, PlanWithActivities,
    BulkMonthlyPlanCreate, BulkCreateResponse
)

router = APIRouter()


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

    # Filtrar por organización
    if current_user.organization_id:
        query = query.filter(MonthlyPlan.organization_id == current_user.organization_id)

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
                "requires_evidence": pa.activity_template.requires_evidence,
                "is_critical": pa.activity_template.is_critical
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
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
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

    # Crear plan
    plan = MonthlyPlan(
        user_id=plan_data.user_id,
        year=plan_data.year,
        month=plan_data.month,
        notes=plan_data.notes,
        status=PlanStatus.DRAFT.value,
        created_by=current_user.id,
        organization_id=plan_data.organization_id or current_user.organization_id
    )

    db.add(plan)
    db.flush()

    # Crear los 4 ciclos semanales
    _create_planning_cycles(db, plan)

    db.commit()
    db.refresh(plan)

    return plan


def _create_planning_cycles(db: Session, plan: MonthlyPlan):
    """Crear los 4 ciclos semanales para un plan mensual."""
    year = plan.year
    month = plan.month

    # Obtener primer y último día del mes
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    # Calcular fechas de cada ciclo (aproximadamente 7 días cada uno)
    total_days = (last_day - first_day).days + 1
    days_per_cycle = total_days // 4

    current_date = first_day
    for cycle_num in range(1, 5):
        start_date = current_date

        if cycle_num == 4:
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


@router.post("/plans/bulk", response_model=BulkCreateResponse)
async def bulk_create_monthly_plans(
    bulk_data: BulkMonthlyPlanCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
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

    # Obtener plantillas activas si se quieren cargar actividades
    templates = []
    if bulk_data.load_activities:
        templates = db.query(ActivityTemplate).filter(
            ActivityTemplate.is_active == True
        ).all()

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
                organization_id=bulk_data.organization_id or current_user.organization_id
            )
            db.add(plan)
            db.flush()

            # Crear los 4 ciclos semanales
            _create_planning_cycles(db, plan)

            # Cargar actividades del catálogo si se solicita
            if bulk_data.load_activities and templates:
                total_plan = 0
                for tmpl in templates:
                    freq = tmpl.default_frequency or 1
                    total_act = freq * 4
                    pa = PlannedActivity(
                        monthly_plan_id=plan.id,
                        activity_template_id=tmpl.id,
                        cycle_1_planned=freq,
                        cycle_2_planned=freq,
                        cycle_3_planned=freq,
                        cycle_4_planned=freq,
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
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
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

    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)

    return plan


@router.post("/plans/{plan_id}/approve")
async def approve_monthly_plan(
    plan_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
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
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
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

    # Verificar que la plantilla existe
    template = db.query(ActivityTemplate).filter(
        ActivityTemplate.id == activity_data.activity_template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla de actividad no encontrada"
        )

    # Calcular totales
    total_planned = (
        activity_data.cycle_1_planned +
        activity_data.cycle_2_planned +
        activity_data.cycle_3_planned +
        activity_data.cycle_4_planned
    )

    planned_activity = PlannedActivity(
        monthly_plan_id=plan_id,
        activity_template_id=activity_data.activity_template_id,
        cycle_1_planned=activity_data.cycle_1_planned,
        cycle_2_planned=activity_data.cycle_2_planned,
        cycle_3_planned=activity_data.cycle_3_planned,
        cycle_4_planned=activity_data.cycle_4_planned,
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
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
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

    for activity_data in bulk_data.activities:
        total_planned = (
            activity_data.cycle_1_planned +
            activity_data.cycle_2_planned +
            activity_data.cycle_3_planned +
            activity_data.cycle_4_planned
        )

        if total_planned > 0:  # Solo agregar si hay algo planeado
            planned_activity = PlannedActivity(
                monthly_plan_id=plan_id,
                activity_template_id=activity_data.activity_template_id,
                cycle_1_planned=activity_data.cycle_1_planned,
                cycle_2_planned=activity_data.cycle_2_planned,
                cycle_3_planned=activity_data.cycle_3_planned,
                cycle_4_planned=activity_data.cycle_4_planned,
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
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
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

    # Guardar totales anteriores
    old_total = activity.total_planned

    # Actualizar campos
    update_data = activity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)

    # Recalcular total
    activity.total_planned = (
        activity.cycle_1_planned +
        activity.cycle_2_planned +
        activity.cycle_3_planned +
        activity.cycle_4_planned
    )

    # Recalcular compliance de la actividad
    if activity.total_planned > 0:
        activity.compliance_percentage = (activity.total_executed / activity.total_planned) * 100
    else:
        activity.compliance_percentage = 0

    # Actualizar plan
    plan = activity.monthly_plan
    plan.total_planned = plan.total_planned - old_total + activity.total_planned
    _recalculate_plan_compliance(plan)

    db.commit()
    db.refresh(activity)

    return activity


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
                "requires_evidence": pa.activity_template.requires_evidence,
                "is_critical": pa.activity_template.is_critical
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
