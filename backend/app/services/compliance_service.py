import json
import logging
from datetime import date, datetime

from sqlalchemy import extract, func
from sqlalchemy.orm import Session, joinedload

from app.models.activity_category import ActivityCategory
from app.models.certification import UserCertification
from app.models.compliance import AnnualSummary, MonthlySummary, Accident
from app.models.emergency import Emergency
from app.models.equipment import Equipment, EquipmentStatus
from app.models.execution import ActivityExecution, ApprovalStatus
from app.models.planning import MonthlyPlan, PlannedActivity
from app.models.user import User

logger = logging.getLogger(__name__)


def _safe_compliance(total_executed: int, total_planned: int) -> float:
    if total_planned <= 0:
        return 0.0
    return (total_executed / total_planned) * 100


def _cycle_from_execution_date(execution_date: date) -> int:
    if execution_date.day <= 10:
        return 1
    if execution_date.day <= 20:
        return 2
    return 3


def recalculate_plan_compliance(db: Session, plan_id: int):
    if not plan_id:
        logger.warning("recalculate_plan_compliance: plan_id=None, abortando")
        return
    """
    Recalcula cumplimiento de un plan mensual:
    - Por actividad (total/ciclos)
    - Por plan (total/compliance)
    Cuenta ejecuciones no rechazadas del plan.
    """
    plan = (
        db.query(MonthlyPlan)
        .options(joinedload(MonthlyPlan.planned_activities))
        .filter(MonthlyPlan.id == plan_id)
        .first()
    )
    if not plan:
        return None

    plan_total_planned = 0
    plan_total_executed = 0

    for activity in plan.planned_activities:
        activity.total_planned = (
            (activity.cycle_1_planned or 0)
            + (activity.cycle_2_planned or 0)
            + (activity.cycle_3_planned or 0)
        )

        counted_executions = (
            db.query(ActivityExecution)
            .filter(
                ActivityExecution.planned_activity_id == activity.id,
                ActivityExecution.approval_status != ApprovalStatus.REJECTED.value,
            )
            .all()
        )

        cycle_counts = {1: 0, 2: 0, 3: 0}
        for execution in counted_executions:
            cycle = execution.cycle_number if execution.cycle_number in (1, 2, 3) else _cycle_from_execution_date(execution.execution_date)
            cycle_counts[cycle] += execution.quantity or 1

        activity.cycle_1_executed = cycle_counts[1]
        activity.cycle_2_executed = cycle_counts[2]
        activity.cycle_3_executed = cycle_counts[3]
        activity.cycle_4_executed = 0
        activity.total_executed = (
            activity.cycle_1_executed
            + activity.cycle_2_executed
            + activity.cycle_3_executed
        )
        activity.compliance_percentage = _safe_compliance(activity.total_executed, activity.total_planned)

        plan_total_planned += activity.total_planned
        plan_total_executed += activity.total_executed

    plan.total_planned = plan_total_planned
    plan.total_executed = plan_total_executed
    plan.compliance_percentage = _safe_compliance(plan.total_executed, plan.total_planned)

    db.commit()
    db.refresh(plan)
    return plan


def recalculate_category_compliance(db: Session, plan_id: int):
    """Calcula cumplimiento por categoría para un plan."""
    plan = (
        db.query(MonthlyPlan)
        .options(
            joinedload(MonthlyPlan.planned_activities).joinedload(PlannedActivity.activity_template)
        )
        .filter(MonthlyPlan.id == plan_id)
        .first()
    )
    if not plan:
        return []

    categories_map = {}
    for activity in plan.planned_activities:
        if not activity.activity_template:
            continue
        category_id = activity.activity_template.category_id
        if category_id not in categories_map:
            categories_map[category_id] = {"total_planned": 0, "total_executed": 0}
        categories_map[category_id]["total_planned"] += activity.total_planned or 0
        categories_map[category_id]["total_executed"] += activity.total_executed or 0

    categories = db.query(ActivityCategory).filter(ActivityCategory.id.in_(list(categories_map.keys()))).all() if categories_map else []
    category_names = {category.id: category.name for category in categories}

    result = []
    for category_id, values in categories_map.items():
        result.append(
            {
                "category_id": category_id,
                "category_name": category_names.get(category_id, "Sin categoria"),
                "total_planned": values["total_planned"],
                "total_executed": values["total_executed"],
                "compliance_percentage": _safe_compliance(values["total_executed"], values["total_planned"]),
            }
        )

    result.sort(key=lambda item: item["category_name"])
    return result


def generate_monthly_summary(db: Session, year: int, month: int, org_id: int):
    """Genera o actualiza el MonthlySummary para el período."""
    today = date.today()

    plans = (
        db.query(MonthlyPlan)
        .filter(
            MonthlyPlan.year == year,
            MonthlyPlan.month == month,
            MonthlyPlan.organization_id == org_id,
        )
        .all()
    )
    total_planned = sum(plan.total_planned or 0 for plan in plans)
    total_executed = sum(plan.total_executed or 0 for plan in plans)
    overall_compliance = _safe_compliance(total_executed, total_planned)

    accidents = (
        db.query(Accident)
        .filter(
            extract("year", Accident.accident_date) == year,
            extract("month", Accident.accident_date) == month,
            Accident.organization_id == org_id,
        )
        .count()
    )

    emergencies_q = db.query(Emergency).filter(
        extract("year", Emergency.reported_at) == year,
        extract("month", Emergency.reported_at) == month,
        Emergency.organization_id == org_id,
    )
    emergencies = emergencies_q.all()
    avg_response_time = None
    response_times = [item.response_time_minutes for item in emergencies if item.response_time_minutes is not None]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)

    all_activities = [activity for plan in plans for activity in plan.planned_activities]
    category_map = {}
    for activity in all_activities:
        if not activity.activity_template:
            continue
        category_id = activity.activity_template.category_id
        key = str(category_id)
        if key not in category_map:
            category_map[key] = {"planned": 0, "executed": 0}
        category_map[key]["planned"] += activity.total_planned or 0
        category_map[key]["executed"] += activity.total_executed or 0
    for key, value in category_map.items():
        value["compliance"] = _safe_compliance(value["executed"], value["planned"])

    active_employees = (
        db.query(User)
        .filter(User.organization_id == org_id, User.is_active.is_(True))
        .count()
    )

    employees_with_expired_certs = (
        db.query(func.count(func.distinct(UserCertification.user_id)))
        .filter(
            UserCertification.organization_id == org_id,
            UserCertification.expiry_date < today,
        )
        .scalar()
        or 0
    )

    equipment_q = db.query(Equipment).filter(
        Equipment.organization_id == org_id,
        Equipment.is_active.is_(True),
    )
    equipment_list = equipment_q.all()
    equipment_in_maintenance = sum(1 for item in equipment_list if item.status == EquipmentStatus.IN_MAINTENANCE.value)
    equipment_out_of_service = sum(1 for item in equipment_list if item.status == EquipmentStatus.OUT_OF_SERVICE.value)

    from datetime import timedelta
    expiring_certs_30 = (
        db.query(UserCertification)
        .filter(
            UserCertification.organization_id == org_id,
            UserCertification.expiry_date >= today,
            UserCertification.expiry_date <= today + timedelta(days=30),
        )
        .count()
    )
    expired_certs = (
        db.query(UserCertification)
        .filter(
            UserCertification.organization_id == org_id,
            UserCertification.expiry_date < today,
        )
        .count()
    )

    summary = (
        db.query(MonthlySummary)
        .filter(
            MonthlySummary.year == year,
            MonthlySummary.month == month,
            MonthlySummary.organization_id == org_id,
        )
        .first()
    )
    if not summary:
        summary = MonthlySummary(year=year, month=month, organization_id=org_id)
        db.add(summary)

    summary.total_accidents = accidents
    summary.total_emergencies = len(emergencies)
    summary.avg_response_time = avg_response_time
    summary.total_planned_activities = total_planned
    summary.total_executed_activities = total_executed
    summary.overall_compliance = overall_compliance
    summary.compliance_by_category = json.dumps(category_map, ensure_ascii=False)
    summary.active_employees = active_employees
    summary.employees_with_expired_certs = employees_with_expired_certs
    summary.total_equipment = len(equipment_list)
    summary.equipment_in_maintenance = equipment_in_maintenance
    summary.equipment_out_of_service = equipment_out_of_service
    summary.expiring_certs_30_days = expiring_certs_30
    summary.expired_certs = expired_certs
    summary.generated_at = datetime.utcnow()

    db.commit()
    db.refresh(summary)
    return summary


def generate_annual_summary(db: Session, year: int, org_id: int):
    """Genera o actualiza AnnualSummary promediando los 12 meses."""
    monthly_compliance = {}
    monthly_values = []

    for month in range(1, 13):
        plans = (
            db.query(MonthlyPlan)
            .filter(
                MonthlyPlan.organization_id == org_id,
                MonthlyPlan.year == year,
                MonthlyPlan.month == month,
            )
            .all()
        )
        total_planned = sum(plan.total_planned or 0 for plan in plans)
        total_executed = sum(plan.total_executed or 0 for plan in plans)
        compliance = _safe_compliance(total_executed, total_planned)
        monthly_compliance[str(month)] = round(compliance, 2)
        monthly_values.append(compliance)

    overall_compliance = sum(monthly_values) / 12 if monthly_values else 0.0

    accidents = (
        db.query(Accident)
        .filter(
            extract("year", Accident.accident_date) == year,
            Accident.organization_id == org_id,
        )
        .count()
    )

    emergencies_q = db.query(Emergency).filter(
        extract("year", Emergency.reported_at) == year,
        Emergency.organization_id == org_id,
    )
    emergencies = emergencies_q.all()
    avg_response_time = None
    response_times = [item.response_time_minutes for item in emergencies if item.response_time_minutes is not None]
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)

    plans_year = (
        db.query(MonthlyPlan)
        .options(joinedload(MonthlyPlan.planned_activities).joinedload(PlannedActivity.activity_template))
        .filter(
            MonthlyPlan.organization_id == org_id,
            MonthlyPlan.year == year,
        )
        .all()
    )
    category_map = {}
    for plan in plans_year:
        for activity in plan.planned_activities:
            if not activity.activity_template:
                continue
            category_id = str(activity.activity_template.category_id)
            if category_id not in category_map:
                category_map[category_id] = {"planned": 0, "executed": 0}
            category_map[category_id]["planned"] += activity.total_planned or 0
            category_map[category_id]["executed"] += activity.total_executed or 0
    for key, value in category_map.items():
        value["compliance"] = _safe_compliance(value["executed"], value["planned"])

    summary = (
        db.query(AnnualSummary)
        .filter(
            AnnualSummary.year == year,
            AnnualSummary.organization_id == org_id,
        )
        .first()
    )
    if not summary:
        summary = AnnualSummary(year=year, organization_id=org_id)
        db.add(summary)

    summary.total_accidents = accidents
    summary.total_emergencies = len(emergencies)
    summary.avg_response_time = avg_response_time
    summary.overall_compliance = overall_compliance
    summary.compliance_by_month = json.dumps(monthly_compliance, ensure_ascii=False)
    summary.compliance_by_category = json.dumps(category_map, ensure_ascii=False)

    db.commit()
    db.refresh(summary)
    return summary
