from datetime import date, datetime
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.certification import UserCertification, VehicleDocument
from app.models.compliance import Accident
from app.models.emergency import Emergency
from app.models.equipment import Equipment
from app.models.planning import MonthlyPlan
from app.models.user import User, UserRole

router = APIRouter()

MONTH_NAMES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def _validate_report_type(report_type: str):
    allowed = {"compliance", "emergencies", "equipment", "certifications", "summary"}
    if report_type not in allowed:
        raise HTTPException(status_code=400, detail="Tipo de reporte no valido")


# M-2: Tipos de reporte permitidos para TAE/PSE (solo sus propios datos individuales)
_TAE_PSE_ALLOWED_REPORT_TYPES = {"compliance"}


def _apply_role_restrictions(current_user: User, report_type: str, user_id: Optional[int]) -> Optional[int]:
    """
    M-2: Para roles TAE y PSE:
    - Solo se permiten tipos de reporte individuales (compliance).
    - Fuerza user_id al propio usuario, ignorando cualquier valor externo.
    Retorna el user_id efectivo a utilizar en la consulta.
    """
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        if report_type not in _TAE_PSE_ALLOWED_REPORT_TYPES:
            raise HTTPException(
                status_code=403,
                detail="No autorizado para este tipo de reporte"
            )
        # Forzar siempre sus propios datos, sin importar el parámetro recibido
        return current_user.id
    return user_id


def _report_columns(report_type: str):
    columns_map = {
        "compliance": [
            {"key": "usuario", "label": "Usuario"},
            {"key": "categoria", "label": "Categoria"},
            {"key": "actividad", "label": "Actividad"},
            {"key": "ciclo_1_plan", "label": "C1 Plan"},
            {"key": "ciclo_1_ejec", "label": "C1 Ejec"},
            {"key": "ciclo_2_plan", "label": "C2 Plan"},
            {"key": "ciclo_2_ejec", "label": "C2 Ejec"},
            {"key": "ciclo_3_plan", "label": "C3 Plan"},
            {"key": "ciclo_3_ejec", "label": "C3 Ejec"},
            {"key": "total_planeado", "label": "Total Plan"},
            {"key": "total_ejecutado", "label": "Total Ejec"},
            {"key": "cumplimiento", "label": "Cumplimiento %"},
        ],
        "emergencies": [
            {"key": "codigo", "label": "Codigo"},
            {"key": "tipo", "label": "Tipo"},
            {"key": "fecha", "label": "Fecha"},
            {"key": "ubicacion", "label": "Ubicacion"},
            {"key": "titulo", "label": "Titulo"},
            {"key": "severidad", "label": "Severidad"},
            {"key": "tiempo_respuesta_min", "label": "T. Respuesta (min)"},
            {"key": "estado", "label": "Estado"},
            {"key": "reportado_por", "label": "Reportado por"},
        ],
        "equipment": [
            {"key": "codigo", "label": "Codigo"},
            {"key": "nombre", "label": "Nombre"},
            {"key": "categoria", "label": "Categoria"},
            {"key": "marca", "label": "Marca"},
            {"key": "modelo", "label": "Modelo"},
            {"key": "serie", "label": "Serie"},
            {"key": "estado", "label": "Estado"},
            {"key": "ubicacion", "label": "Ubicacion"},
            {"key": "proximo_mantenimiento", "label": "Prox. Mantenimiento"},
        ],
        "certifications": [
            {"key": "tipo_registro", "label": "Tipo"},
            {"key": "usuario_equipo", "label": "Usuario/Equipo"},
            {"key": "certificacion", "label": "Certificacion"},
            {"key": "fecha_emision", "label": "Fecha Emision"},
            {"key": "fecha_vencimiento", "label": "Fecha Vencimiento"},
            {"key": "dias_restantes", "label": "Dias Restantes"},
            {"key": "estado", "label": "Estado"},
            {"key": "entidad", "label": "Entidad"},
        ],
        "summary": [
            {"key": "indicador", "label": "Indicador"},
            {"key": "valor", "label": "Valor"},
        ],
    }
    return columns_map[report_type]


def _get_compliance_data(db: Session, year: int, month: int, org_id, user_id: Optional[int] = None):
    plans_q = db.query(MonthlyPlan).filter(MonthlyPlan.year == year, MonthlyPlan.month == month)
    if org_id is not None:
        plans_q = plans_q.filter(MonthlyPlan.organization_id == org_id)
    if user_id:
        plans_q = plans_q.filter(MonthlyPlan.user_id == user_id)

    rows = []
    plans = plans_q.all()
    for plan in plans:
        user_name = plan.user.full_name if plan.user else "Sin asignar"
        for activity in plan.planned_activities:
            if not activity.activity_template:
                continue
            category_name = activity.activity_template.category.name if activity.activity_template.category else "Sin categoria"
            compliance = (activity.total_executed / activity.total_planned * 100) if activity.total_planned > 0 else 0
            rows.append(
                {
                    "usuario": user_name,
                    "categoria": category_name,
                    "actividad": activity.activity_template.name,
                    "ciclo_1_plan": activity.cycle_1_planned,
                    "ciclo_1_ejec": activity.cycle_1_executed,
                    "ciclo_2_plan": activity.cycle_2_planned,
                    "ciclo_2_ejec": activity.cycle_2_executed,
                    "ciclo_3_plan": activity.cycle_3_planned,
                    "ciclo_3_ejec": activity.cycle_3_executed,
                    "total_planeado": activity.total_planned,
                    "total_ejecutado": activity.total_executed,
                    "cumplimiento": round(compliance, 1),
                }
            )
    return rows, plans


def _get_emergencies_data(db: Session, year: int, month: Optional[int], org_id):
    query = db.query(Emergency).filter(extract("year", Emergency.reported_at) == year)
    if month:
        query = query.filter(extract("month", Emergency.reported_at) == month)
    if org_id is not None:
        query = query.filter(Emergency.organization_id == org_id)

    rows = []
    for emergency in query.all():
        reporter = db.query(User).filter(User.id == emergency.reported_by).first() if emergency.reported_by else None
        rows.append(
            {
                "codigo": emergency.emergency_code or "",
                "tipo": emergency.emergency_type.name if emergency.emergency_type else "",
                "fecha": emergency.reported_at.strftime("%d/%m/%Y %H:%M") if emergency.reported_at else "",
                "ubicacion": emergency.location or "",
                "titulo": emergency.title or "",
                "severidad": emergency.severity or "",
                "tiempo_respuesta_min": emergency.response_time_minutes or 0,
                "estado": emergency.status or "",
                "reportado_por": reporter.full_name if reporter else "",
            }
        )
    return rows


def _get_equipment_data(db: Session, org_id):
    query = db.query(Equipment).filter(Equipment.is_active.is_(True))
    if org_id is not None:
        query = query.filter(Equipment.organization_id == org_id)

    rows = []
    for equipment in query.all():
        rows.append(
            {
                "codigo": equipment.code or "",
                "nombre": equipment.name or "",
                "categoria": equipment.category.name if equipment.category else "",
                "marca": equipment.brand or "",
                "modelo": equipment.model or "",
                "serie": equipment.serial_number or "",
                "estado": equipment.status or "",
                "ubicacion": equipment.location or "",
                "proximo_mantenimiento": equipment.next_maintenance_date.strftime("%d/%m/%Y") if equipment.next_maintenance_date else "N/A",
            }
        )
    return rows


def _get_certifications_data(db: Session, org_id):
    rows = []
    today = date.today()

    user_certs_q = db.query(UserCertification)
    if org_id is not None:
        user_certs_q = user_certs_q.filter(UserCertification.organization_id == org_id)

    for cert in user_certs_q.all():
        days_left = (cert.expiry_date - today).days if cert.expiry_date else None
        if days_left is None:
            status = "SIN FECHA"
        elif days_left < 0:
            status = "VENCIDA"
        elif days_left <= 7:
            status = "CRITICA"
        elif days_left <= 15:
            status = "URGENTE"
        elif days_left <= 30:
            status = "POR VENCER"
        else:
            status = "VIGENTE"

        rows.append(
            {
                "tipo_registro": "Usuario",
                "usuario_equipo": cert.user.full_name if cert.user else "",
                "certificacion": cert.certification_type.name if cert.certification_type else "",
                "fecha_emision": cert.issue_date.strftime("%d/%m/%Y") if cert.issue_date else "",
                "fecha_vencimiento": cert.expiry_date.strftime("%d/%m/%Y") if cert.expiry_date else "",
                "dias_restantes": days_left if days_left is not None else "",
                "estado": status,
                "entidad": cert.issuing_entity or "",
            }
        )

    vehicle_docs_q = db.query(VehicleDocument)
    if org_id is not None:
        vehicle_docs_q = vehicle_docs_q.filter(VehicleDocument.organization_id == org_id)

    equipment_ids = [item.equipment_id for item in vehicle_docs_q.all() if item.equipment_id]
    equipment_map = {}
    if equipment_ids:
        equipment_map = {eq.id: eq for eq in db.query(Equipment).filter(Equipment.id.in_(equipment_ids)).all()}

    for doc in vehicle_docs_q.all():
        days_left = (doc.expiry_date - today).days if doc.expiry_date else None
        if days_left is None:
            status = "SIN FECHA"
        elif days_left < 0:
            status = "VENCIDA"
        elif days_left <= 7:
            status = "CRITICA"
        elif days_left <= 15:
            status = "URGENTE"
        elif days_left <= 30:
            status = "POR VENCER"
        else:
            status = "VIGENTE"

        equipment = equipment_map.get(doc.equipment_id)
        equipment_name = equipment.name if equipment else f"Equipo {doc.equipment_id}" if doc.equipment_id else ""

        rows.append(
            {
                "tipo_registro": "Vehiculo",
                "usuario_equipo": equipment_name,
                "certificacion": doc.document_type.name if doc.document_type else "",
                "fecha_emision": doc.issue_date.strftime("%d/%m/%Y") if doc.issue_date else "",
                "fecha_vencimiento": doc.expiry_date.strftime("%d/%m/%Y") if doc.expiry_date else "",
                "dias_restantes": days_left if days_left is not None else "",
                "estado": status,
                "entidad": doc.issuing_entity or "",
            }
        )

    return rows


def _get_summary_data(db: Session, year: int, month: Optional[int], org_id, user_id: Optional[int] = None):
    selected_month = month or datetime.now().month

    compliance_rows, plans = _get_compliance_data(db, year, selected_month, org_id, user_id)
    total_planned = sum(item["total_planeado"] for item in compliance_rows)
    total_executed = sum(item["total_ejecutado"] for item in compliance_rows)
    compliance_pct = (total_executed / total_planned * 100) if total_planned > 0 else 0

    accidents_q = db.query(Accident).filter(
        extract("year", Accident.accident_date) == year,
        extract("month", Accident.accident_date) == selected_month,
    )
    if org_id is not None:
        accidents_q = accidents_q.filter(Accident.organization_id == org_id)

    emergencies_q = db.query(Emergency).filter(
        extract("year", Emergency.reported_at) == year,
        extract("month", Emergency.reported_at) == selected_month,
    )
    if org_id is not None:
        emergencies_q = emergencies_q.filter(Emergency.organization_id == org_id)

    certs = _get_certifications_data(db, org_id)
    certs_expiring = sum(1 for item in certs if isinstance(item.get("dias_restantes"), int) and 0 <= item["dias_restantes"] <= 30)
    certs_expired = sum(1 for item in certs if isinstance(item.get("dias_restantes"), int) and item["dias_restantes"] < 0)

    return [
        {"indicador": "Periodo", "valor": f"{MONTH_NAMES[selected_month]} {year}"},
        {"indicador": "Accidentes", "valor": str(accidents_q.count())},
        {"indicador": "Emergencias", "valor": str(emergencies_q.count())},
        {"indicador": "Actividades Planeadas", "valor": str(total_planned)},
        {"indicador": "Actividades Ejecutadas", "valor": str(total_executed)},
        {"indicador": "Cumplimiento General", "valor": f"{compliance_pct:.1f}%"},
        {"indicador": "Usuarios con Plan", "valor": str(len(plans))},
        {"indicador": "Certificaciones por vencer (<=30d)", "valor": str(certs_expiring)},
        {"indicador": "Certificaciones vencidas", "valor": str(certs_expired)},
    ]


def _get_report_rows(db: Session, report_type: str, year: int, month: Optional[int], org_id, user_id: Optional[int]):
    selected_month = month or datetime.now().month
    if report_type == "compliance":
        rows, _ = _get_compliance_data(db, year, selected_month, org_id, user_id)
        return rows
    if report_type == "emergencies":
        return _get_emergencies_data(db, year, month, org_id)
    if report_type == "equipment":
        return _get_equipment_data(db, org_id)
    if report_type == "certifications":
        return _get_certifications_data(db, org_id)
    return _get_summary_data(db, year, selected_month, org_id, user_id)


@router.get("/types")
async def get_report_types(current_user: User = Depends(get_current_user)):
    all_types = [
        {
            "id": "compliance",
            "name": "Cumplimiento Mensual",
            "description": "Reporte detallado de cumplimiento planeado vs ejecutado por usuario y categoria",
            "formats": ["excel", "pdf"],
        },
        {
            "id": "emergencies",
            "name": "Emergencias",
            "description": "Listado de emergencias con tiempos de respuesta y detalles",
            "formats": ["excel", "pdf"],
        },
        {
            "id": "equipment",
            "name": "Inventario de Equipos",
            "description": "Estado actual del inventario de equipos de seguridad",
            "formats": ["excel", "pdf"],
        },
        {
            "id": "certifications",
            "name": "Certificaciones y Vencimientos",
            "description": "Estado de certificaciones del personal y vehiculos con alertas de vencimiento",
            "formats": ["excel", "pdf"],
        },
        {
            "id": "summary",
            "name": "Resumen Ejecutivo",
            "description": "KPIs principales, cumplimiento general y alertas del periodo",
            "formats": ["excel", "pdf"],
        },
    ]
    # M-2: TAE y PSE solo ven los tipos de reporte que les corresponden
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        return [t for t in all_types if t["id"] in _TAE_PSE_ALLOWED_REPORT_TYPES]
    return all_types


@router.get("/preview/{report_type}")
async def preview_report(
    report_type: str,
    year: int = Query(..., ge=2020, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_report_type(report_type)
    # M-2: Aplicar restricciones de rol (TAE/PSE solo compliance, solo sus datos)
    effective_user_id = _apply_role_restrictions(current_user, report_type, user_id)
    org_id = current_user.organization_id
    columns = _report_columns(report_type)
    rows = _get_report_rows(db, report_type, year, month, org_id, effective_user_id)

    return {
        "type": report_type,
        "columns": columns,
        "data": rows,
        "total": len(rows),
    }


@router.get("/export/{report_type}")
async def export_report(
    report_type: str,
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    year: int = Query(..., ge=2020, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_report_type(report_type)
    # M-2: Aplicar restricciones de rol (TAE/PSE solo compliance, solo sus datos)
    effective_user_id = _apply_role_restrictions(current_user, report_type, user_id)
    if format == "excel":
        return _export_excel(db, report_type, year, month, current_user, effective_user_id)
    return _export_pdf(db, report_type, year, month, current_user, effective_user_id)


def _export_excel(db: Session, report_type: str, year: int, month: Optional[int], current_user: User, user_id: Optional[int]):
    rows = _get_report_rows(db, report_type, year, month, current_user.organization_id, user_id)
    columns = _report_columns(report_type)
    headers = [column["label"] for column in columns]
    keys = [column["key"] for column in columns]

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = report_type.capitalize()

    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    title_font = Font(name="Calibri", bold=True, size=14, color="1F4E79")
    subtitle_font = Font(name="Calibri", size=11, color="666666")
    border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    fill_green = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
    fill_orange = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
    fill_red = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    period = f"{MONTH_NAMES[month] if month else 'Anual'} {year}"

    last_col = max(1, len(headers))
    sheet.merge_cells(f"A1:{get_column_letter(last_col)}1")
    sheet["A1"] = f"Gestion GAE - Reporte de {report_type.title()}"
    sheet["A1"].font = title_font
    sheet["A2"] = f"Periodo: {period} | Generado: {now_str}"
    sheet["A2"].font = subtitle_font

    row_start = 4
    for col_index, header in enumerate(headers, 1):
        cell = sheet.cell(row=row_start, column=col_index, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    for row_index, row_data in enumerate(rows, row_start + 1):
        for col_index, key in enumerate(keys, 1):
            value = row_data.get(key, "")
            cell = sheet.cell(row=row_index, column=col_index, value=value)
            cell.border = border
            cell.alignment = Alignment(vertical="center")

            if key == "cumplimiento" and isinstance(value, (int, float)):
                cell.value = value / 100
                cell.number_format = "0.0%"
                if value >= 80:
                    cell.fill = fill_green
                elif value >= 50:
                    cell.fill = fill_orange
                else:
                    cell.fill = fill_red

    for col_index in range(1, len(headers) + 1):
        max_length = len(headers[col_index - 1])
        for row in range(1, sheet.max_row + 1):
            value = sheet.cell(row=row, column=col_index).value
            if value is not None:
                max_length = max(max_length, len(str(value)))
        sheet.column_dimensions[get_column_letter(col_index)].width = min(max_length + 2, 45)

    sheet.freeze_panes = f"A{row_start + 1}"

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)

    filename = f"reporte_{report_type}_{year}{f'_{month}' if month else ''}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _export_pdf(db: Session, report_type: str, year: int, month: Optional[int], current_user: User, user_id: Optional[int]):
    rows = _get_report_rows(db, report_type, year, month, current_user.organization_id, user_id)
    columns = _report_columns(report_type)
    period = f"{MONTH_NAMES[month] if month else 'Anual'} {year}"
    pdf_bytes = _generate_pdf(
        report_type,
        {
            "columns": columns,
            "data": rows,
            "total": len(rows),
            "period": period,
        },
    )

    filename = f"reporte_{report_type}_{year}{f'_{month}' if month else ''}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _generate_pdf(report_type: str, data: dict) -> bytes:
    """Genera PDF compacto, legible y bien formateado para todos los tipos de reporte."""
    buffer = io.BytesIO()

    columns = data.get("columns", [])
    num_cols = len(columns)

    # Siempre usar landscape para mejorar legibilidad de tablas
    page_size = landscape(A4)
    margin = 1.5 * cm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    page_width = page_size[0] - 2 * margin
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#1a3a5c"),
        spaceAfter=4,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        wordWrap="CJK",
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    report_names = {
        "compliance": "Reporte de Cumplimiento Mensual",
        "emergencies": "Reporte de Emergencias",
        "equipment": "Inventario de Equipos",
        "certifications": "Certificaciones y Vencimientos",
        "summary": "Resumen Ejecutivo",
    }
    title_text = report_names.get(report_type, f"Reporte: {report_type}")

    col_weights = {
        "compliance": [9, 10, 34, 5, 5, 5, 5, 5, 5, 6, 6, 10],
        "emergencies": [7, 10, 10, 16, 22, 8, 9, 8, 10],
        "equipment": [7, 18, 12, 10, 10, 10, 8, 14, 11],
        "certifications": [8, 16, 20, 10, 10, 8, 8, 12],
        "summary": [60, 40],
    }

    default_weights = [1] * max(num_cols, 1)
    weights = col_weights.get(report_type, default_weights)
    if len(weights) < num_cols:
        weights = weights + [1] * (num_cols - len(weights))

    selected_weights = weights[:num_cols]
    clean_weights = [weight if isinstance(weight, (int, float)) and weight is not None else 1 for weight in selected_weights]
    total_weight = sum(clean_weights) if sum(clean_weights) > 0 else max(num_cols, 1)
    col_widths = [page_width * (weight / total_weight) for weight in clean_weights]

    header_abbrev = {
        "compliance": {
            "Cumplimiento %": "Cumpl.%",
            "Total Plan": "T.Plan",
            "Total Ejec": "T.Ejec",
            "Categoria": "Cat.",
        }
    }

    def get_col_label(current_report_type: str, label: str) -> str:
        return header_abbrev.get(current_report_type, {}).get(label, label)

    header_row = [Paragraph(get_col_label(report_type, col["label"]), header_cell_style) for col in columns]
    rows = [header_row]
    row_data = data.get("data", [])
    cat_abbrev = {
        "SISTEMA DE INTEGRIDAD OPERACIONAL": "SIO",
        "ACTIVIDADES DIARIAS": "ACTIVIDADES",
        "INSPECCIONES": "INSPECCIONES",
        "Entrenamiento": "Entrenam.",
    }

    empty_cells = set()  # (row_idx, col_idx) de celdas vacías para SPAN
    prev_usuario = ""
    prev_categoria = ""

    for rec_idx, record in enumerate(row_data):
        row_idx = rec_idx + 1  # +1 por el header
        row = []
        for col_i, col in enumerate(columns):
            val = record.get(col["key"], "")
            if val is None:
                val = ""
            elif isinstance(val, float):
                val = f"{val:.1f}"
            elif not isinstance(val, str):
                val = str(val)

            if report_type == "compliance" and col["key"] == "categoria":
                val = cat_abbrev.get(val, val)

            if report_type == "compliance":
                if col["key"] == "usuario":
                    if val == prev_usuario and prev_usuario != "":
                        empty_cells.add((row_idx, col_i))
                        val = ""
                    else:
                        prev_usuario = val
                        prev_categoria = ""
                elif col["key"] == "categoria":
                    if val == prev_categoria and prev_categoria != "":
                        empty_cells.add((row_idx, col_i))
                        val = ""
                    else:
                        prev_categoria = val

            if col["key"] == "cumplimiento" and val and val != "":
                try:
                    pct = float(str(val).replace("%", "").strip())
                    if pct >= 80:
                        color_hex = "#276221"
                    elif pct >= 50:
                        color_hex = "#7d5a00"
                    else:
                        color_hex = "#8b1a1a"
                    display_value = val if str(val).endswith("%") else f"{val}%"
                    paragraph = Paragraph(f'<font color="{color_hex}">{display_value}</font>', cell_style)
                except (ValueError, TypeError):
                    paragraph = Paragraph(str(val), cell_style)
            else:
                paragraph = Paragraph(val, cell_style)
            row.append(paragraph)
        rows.append(row)

    table = Table(rows, colWidths=col_widths, repeatRows=1)

    primary_color = colors.HexColor("#1a3a5c")
    alt_row_color = colors.HexColor("#f0f4f8")
    white = colors.white
    table_style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ]

    for row_index in range(1, len(rows)):
        if row_index % 2 == 0:
            table_style_cmds.append(("BACKGROUND", (0, row_index), (-1, row_index), alt_row_color))
        else:
            table_style_cmds.append(("BACKGROUND", (0, row_index), (-1, row_index), white))

    numeric_keys = {
        "compliance": list(range(3, 12)),
        "emergencies": [6],
        "equipment": [],
        "certifications": [5],
        "summary": [1],
    }
    for col_index in numeric_keys.get(report_type, []):
        if col_index < num_cols:
            table_style_cmds.append(("ALIGN", (col_index, 1), (col_index, -1), "CENTER"))

    if report_type == "compliance" and len(rows) > 1:
        # Sin SPAN — solo eliminar bordes internos en celdas vacías de col 0 y 1
        # y agregar líneas separadoras entre grupos de usuario
        for row_idx in range(2, len(rows)):
            # Si col 0 NO está vacía → es un nuevo usuario → línea separadora
            if (row_idx, 0) not in empty_cells:
                table_style_cmds.append(
                    ("LINEABOVE", (0, row_idx), (-1, row_idx), 1.2, colors.HexColor("#1a3a5c"))
                )
            # Para celdas vacías de col 0 y col 1: quitar borde superior e inferior
            for col_idx in [0, 1]:
                if (row_idx, col_idx) in empty_cells:
                    table_style_cmds.append(
                        ("INNERGRID", (col_idx, row_idx), (col_idx, row_idx), 0, colors.white)
                    )
                    table_style_cmds.append(
                        ("BOX", (col_idx, row_idx), (col_idx, row_idx), 0, colors.white)
                    )

    table.setStyle(TableStyle(table_style_cmds))

    total_records = data.get("total", len(row_data))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#999999"),
        alignment=TA_RIGHT,
    )

    logo_style = ParagraphStyle(
        "Logo",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    )

    story = [
        Paragraph("Gestión GAE", logo_style),
        Spacer(1, 2 * mm),
        Paragraph(title_text, title_style),
        Paragraph(f"Período: {data.get('period', '')}  |  Total registros: {total_records}", subtitle_style),
        HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8),
        table,
        Spacer(1, 4 * mm),
        Paragraph(f"Generado por Gestión GAE  •  {total_records} registros", footer_style),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
