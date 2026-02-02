from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from typing import Optional
from datetime import date, datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.planning import MonthlyPlan, PlannedActivity
from app.models.execution import ActivityExecution
from app.models.emergency import Emergency, EmergencyStatus
from app.models.equipment import Equipment, EquipmentStatus
from app.models.certification import UserCertification
from app.models.compliance import Accident
from app.models.activity_category import ActivityCategory
from app.schemas.dashboard import (
    DashboardData, MainKPIs, KPICard,
    ComplianceSummary, ComplianceByCategory, MonthlyCompliance,
    EmergencySummary, EmergencyByType,
    AlertsSummary, Alert,
    TopPerformersSummary, TopPerformer,
    EquipmentStatusSummary, CertificationStatusSummary
)

router = APIRouter()

MONTH_NAMES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


@router.get("/", response_model=DashboardData)
async def get_dashboard(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener datos completos del dashboard."""
    org_id = current_user.organization_id
    today = date.today()

    # ==========================================
    # KPIs PRINCIPALES
    # ==========================================

    # Accidentes del mes
    accidents_count = db.query(Accident).filter(
        Accident.organization_id == org_id,
        extract('year', Accident.accident_date) == year,
        extract('month', Accident.accident_date) == month
    ).count()

    # Emergencias del mes
    emergencies_count = db.query(Emergency).filter(
        Emergency.organization_id == org_id,
        extract('year', Emergency.reported_at) == year,
        extract('month', Emergency.reported_at) == month
    ).count()

    # Cumplimiento general
    plans = db.query(MonthlyPlan).filter(
        MonthlyPlan.organization_id == org_id,
        MonthlyPlan.year == year,
        MonthlyPlan.month == month
    ).all()

    total_planned = sum(p.total_planned for p in plans)
    total_executed = sum(p.total_executed for p in plans)
    overall_compliance = (total_executed / total_planned * 100) if total_planned > 0 else 0

    # Actividades pendientes
    pending_activities = total_planned - total_executed

    main_kpis = MainKPIs(
        accidents=KPICard(
            title="Accidentes",
            value=accidents_count,
            icon="SafetyOutlined",
            color="#ff4d4f" if accidents_count > 0 else "#52c41a"
        ),
        emergencies=KPICard(
            title="Emergencias",
            value=emergencies_count,
            icon="AlertOutlined",
            color="#fa8c16"
        ),
        compliance=KPICard(
            title="Cumplimiento",
            value=round(overall_compliance, 1),
            unit="%",
            icon="CheckCircleOutlined",
            color="#52c41a" if overall_compliance >= 80 else ("#faad14" if overall_compliance >= 50 else "#ff4d4f")
        ),
        pending_activities=KPICard(
            title="Pendientes",
            value=pending_activities,
            icon="ClockCircleOutlined",
            color="#1890ff"
        )
    )

    # ==========================================
    # CUMPLIMIENTO POR CATEGORÍA
    # ==========================================

    categories = db.query(ActivityCategory).filter(ActivityCategory.is_active == True).all()
    compliance_by_category = []

    for cat in categories:
        # Sumar planeado y ejecutado de todas las actividades de esta categoría
        cat_planned = 0
        cat_executed = 0

        for plan in plans:
            for pa in plan.planned_activities:
                if pa.activity_template and pa.activity_template.category_id == cat.id:
                    cat_planned += pa.total_planned
                    cat_executed += pa.total_executed

        compliance_by_category.append(ComplianceByCategory(
            category_id=cat.id,
            category_name=cat.name,
            category_code=cat.code,
            category_color=cat.color,
            total_planned=cat_planned,
            total_executed=cat_executed,
            compliance_percentage=round((cat_executed / cat_planned * 100) if cat_planned > 0 else 0, 1)
        ))

    # Tendencia mensual (últimos 6 meses)
    monthly_trend = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1

        month_plans = db.query(MonthlyPlan).filter(
            MonthlyPlan.organization_id == org_id,
            MonthlyPlan.year == y,
            MonthlyPlan.month == m
        ).all()

        mp = sum(p.total_planned for p in month_plans)
        me = sum(p.total_executed for p in month_plans)

        monthly_trend.append(MonthlyCompliance(
            year=y,
            month=m,
            month_name=MONTH_NAMES[m],
            compliance_percentage=round((me / mp * 100) if mp > 0 else 0, 1)
        ))

    compliance = ComplianceSummary(
        overall_compliance=round(overall_compliance, 1),
        by_category=compliance_by_category,
        by_cycle=[],
        monthly_trend=monthly_trend
    )

    # ==========================================
    # EMERGENCIAS
    # ==========================================

    emergencies = db.query(Emergency).filter(
        Emergency.organization_id == org_id,
        extract('year', Emergency.reported_at) == year,
        extract('month', Emergency.reported_at) == month
    ).all()

    by_type_dict = {}
    total_response = 0
    count_response = 0

    for e in emergencies:
        if e.emergency_type_id not in by_type_dict:
            by_type_dict[e.emergency_type_id] = 0
        by_type_dict[e.emergency_type_id] += 1

        if e.response_time_minutes:
            total_response += e.response_time_minutes
            count_response += 1

    emergencies_summary = EmergencySummary(
        total=len(emergencies),
        by_type=[],  # Simplificado
        avg_response_time=round(total_response / count_response, 1) if count_response > 0 else None,
        this_month=len(emergencies),
        vs_last_month=None
    )

    # ==========================================
    # ALERTAS
    # ==========================================

    alerts_list = []

    # Certificaciones por vencer
    expiring_certs = db.query(UserCertification).join(User).filter(
        User.organization_id == org_id,
        UserCertification.expiry_date <= date.today() + __import__('datetime').timedelta(days=30),
        UserCertification.expiry_date >= date.today()
    ).limit(10).all()

    for cert in expiring_certs:
        days = (cert.expiry_date - today).days
        alerts_list.append(Alert(
            id=cert.id,
            type="certification",
            priority="critical" if days <= 7 else ("urgent" if days <= 15 else "warning"),
            title=f"Certificación por vencer",
            description=f"Vence en {days} días",
            due_date=cert.expiry_date,
            created_at=datetime.now()
        ))

    alerts_summary = AlertsSummary(
        total=len(alerts_list),
        critical=sum(1 for a in alerts_list if a.priority == "critical"),
        urgent=sum(1 for a in alerts_list if a.priority == "urgent"),
        warning=sum(1 for a in alerts_list if a.priority == "warning"),
        info=sum(1 for a in alerts_list if a.priority == "info"),
        alerts=alerts_list[:10]
    )

    # ==========================================
    # TOP PERFORMERS
    # ==========================================

    top_performers_list = []
    users_compliance = []

    for plan in plans:
        if plan.total_planned > 0:
            users_compliance.append({
                "user_id": plan.user_id,
                "user_name": plan.user.full_name if plan.user else "",
                "compliance": plan.compliance_percentage,
                "executed": plan.total_executed
            })

    users_compliance.sort(key=lambda x: x["compliance"], reverse=True)

    for i, uc in enumerate(users_compliance[:5]):
        top_performers_list.append(TopPerformer(
            user_id=uc["user_id"],
            user_name=uc["user_name"],
            compliance_percentage=round(uc["compliance"], 1),
            total_executed=uc["executed"],
            rank=i + 1
        ))

    top_performers = TopPerformersSummary(top_performers=top_performers_list)

    # ==========================================
    # EQUIPOS
    # ==========================================

    equipment_list = db.query(Equipment).filter(
        Equipment.organization_id == org_id,
        Equipment.is_active == True
    ).all()

    equipment_summary = EquipmentStatusSummary(
        total=len(equipment_list),
        operational=sum(1 for e in equipment_list if e.status == EquipmentStatus.OPERATIONAL.value),
        in_maintenance=sum(1 for e in equipment_list if e.status == EquipmentStatus.IN_MAINTENANCE.value),
        out_of_service=sum(1 for e in equipment_list if e.status == EquipmentStatus.OUT_OF_SERVICE.value),
        pending_maintenance=sum(1 for e in equipment_list if e.next_maintenance_date and e.next_maintenance_date <= today)
    )

    # ==========================================
    # CERTIFICACIONES
    # ==========================================

    all_certs = db.query(UserCertification).join(User).filter(
        User.organization_id == org_id
    ).all()

    cert_summary = CertificationStatusSummary(
        total_personal=len(all_certs),
        expiring_30_days=sum(1 for c in all_certs if 0 < (c.expiry_date - today).days <= 30),
        expiring_15_days=sum(1 for c in all_certs if 0 < (c.expiry_date - today).days <= 15),
        expiring_7_days=sum(1 for c in all_certs if 0 < (c.expiry_date - today).days <= 7),
        expired=sum(1 for c in all_certs if (c.expiry_date - today).days < 0)
    )

    # ==========================================
    # RESPUESTA FINAL
    # ==========================================

    return DashboardData(
        period=f"{MONTH_NAMES[month]} {year}",
        year=year,
        month=month,
        main_kpis=main_kpis,
        compliance=compliance,
        emergencies=emergencies_summary,
        alerts=alerts_summary,
        pending_activities=__import__('app.schemas.dashboard', fromlist=['PendingActivitiesSummary']).PendingActivitiesSummary(
            total_pending=pending_activities,
            activities=[]
        ),
        top_performers=top_performers,
        equipment=equipment_summary,
        certifications=cert_summary,
        generated_at=datetime.utcnow()
    )


@router.get("/compliance-chart")
async def get_compliance_chart_data(
    year: int = Query(..., ge=2020, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener datos para gráfico de cumplimiento anual."""
    org_id = current_user.organization_id
    data = []

    for month in range(1, 13):
        plans = db.query(MonthlyPlan).filter(
            MonthlyPlan.organization_id == org_id,
            MonthlyPlan.year == year,
            MonthlyPlan.month == month
        ).all()

        total_planned = sum(p.total_planned for p in plans)
        total_executed = sum(p.total_executed for p in plans)
        compliance = (total_executed / total_planned * 100) if total_planned > 0 else 0

        data.append({
            "month": month,
            "month_name": MONTH_NAMES[month],
            "planned": total_planned,
            "executed": total_executed,
            "compliance": round(compliance, 1)
        })

    return data
