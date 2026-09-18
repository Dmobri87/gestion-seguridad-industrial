from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import Optional
from datetime import date, datetime
import io
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.planning import MonthlyPlan, PlannedActivity
from app.models.execution import ActivityExecution
from app.models.emergency import Emergency
from app.models.equipment import Equipment, EquipmentStatus
from app.models.certification import UserCertification
from app.models.compliance import Accident
from app.models.activity_category import ActivityCategory

router = APIRouter()

MONTH_NAMES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def _get_compliance_data(db: Session, year: int, month: int, org_id, user_id: Optional[int] = None):
    """Obtener datos de cumplimiento para reportes."""
    plans_q = db.query(MonthlyPlan).filter(
        MonthlyPlan.year == year,
        MonthlyPlan.month == month
    )
    if org_id is not None:
        plans_q = plans_q.filter(MonthlyPlan.organization_id == org_id)
    if user_id:
        plans_q = plans_q.filter(MonthlyPlan.user_id == user_id)
    plans = plans_q.all()

    categories = db.query(ActivityCategory).filter(ActivityCategory.is_active == True).all()

    rows = []
    for plan in plans:
        user_name = plan.user.full_name if plan.user else "Sin asignar"
        for pa in plan.planned_activities:
            if pa.activity_template:
                cat = next((c for c in categories if c.id == pa.activity_template.category_id), None)
                cat_name = cat.name if cat else "Sin categoria"
                compliance = (pa.total_executed / pa.total_planned * 100) if pa.total_planned > 0 else 0
                rows.append({
                    "usuario": user_name,
                    "categoria": cat_name,
                    "actividad": pa.activity_template.name,
                    "ciclo_1_plan": pa.cycle_1_planned,
                    "ciclo_1_ejec": pa.cycle_1_executed,
                    "ciclo_2_plan": pa.cycle_2_planned,
                    "ciclo_2_ejec": pa.cycle_2_executed,
                    "ciclo_3_plan": pa.cycle_3_planned,
                    "ciclo_3_ejec": pa.cycle_3_executed,
                    "ciclo_4_plan": pa.cycle_4_planned,
                    "ciclo_4_ejec": pa.cycle_4_executed,
                    "total_planeado": pa.total_planned,
                    "total_ejecutado": pa.total_executed,
                    "cumplimiento": round(compliance, 1),
                })
    return rows, plans


def _get_emergencies_data(db: Session, year: int, month: Optional[int], org_id):
    """Obtener datos de emergencias para reportes."""
    q = db.query(Emergency).filter(extract('year', Emergency.reported_at) == year)
    if month:
        q = q.filter(extract('month', Emergency.reported_at) == month)
    if org_id is not None:
        q = q.filter(Emergency.organization_id == org_id)
    emergencies = q.all()

    rows = []
    for e in emergencies:
        rows.append({
            "codigo": e.code or "",
            "tipo": e.emergency_type.name if e.emergency_type else "",
            "fecha": e.reported_at.strftime("%d/%m/%Y %H:%M") if e.reported_at else "",
            "ubicacion": e.location or "",
            "descripcion": e.description or "",
            "severidad": e.severity or "",
            "tiempo_respuesta_min": e.response_time_minutes or 0,
            "estado": e.status or "",
            "reportado_por": e.reporter.full_name if e.reporter else "",
        })
    return rows


def _get_equipment_data(db: Session, org_id):
    """Obtener datos de equipos para reportes."""
    q = db.query(Equipment).filter(Equipment.is_active == True)
    if org_id is not None:
        q = q.filter(Equipment.organization_id == org_id)
    equipment_list = q.all()

    rows = []
    for eq in equipment_list:
        rows.append({
            "codigo": eq.code or "",
            "nombre": eq.name or "",
            "categoria": eq.category.name if eq.category else "",
            "marca": eq.brand or "",
            "modelo": eq.model or "",
            "serie": eq.serial_number or "",
            "estado": eq.status or "",
            "ubicacion": eq.location or "",
            "proximo_mantenimiento": eq.next_maintenance_date.strftime("%d/%m/%Y") if eq.next_maintenance_date else "N/A",
        })
    return rows


def _get_certifications_data(db: Session, org_id):
    """Obtener datos de certificaciones para reportes."""
    q = db.query(UserCertification).join(User)
    if org_id is not None:
        q = q.filter(User.organization_id == org_id)
    certs = q.all()
    today = date.today()

    rows = []
    for c in certs:
        days_left = (c.expiry_date - today).days if c.expiry_date else None
        if days_left is not None:
            if days_left < 0:
                estado = "VENCIDA"
            elif days_left <= 7:
                estado = "CRITICA"
            elif days_left <= 15:
                estado = "URGENTE"
            elif days_left <= 30:
                estado = "POR VENCER"
            else:
                estado = "VIGENTE"
        else:
            estado = "SIN FECHA"

        rows.append({
            "usuario": c.user.full_name if c.user else "",
            "certificacion": c.certification_type.name if c.certification_type else "",
            "fecha_emision": c.issue_date.strftime("%d/%m/%Y") if c.issue_date else "",
            "fecha_vencimiento": c.expiry_date.strftime("%d/%m/%Y") if c.expiry_date else "",
            "dias_restantes": days_left if days_left is not None else "",
            "estado": estado,
            "entidad": c.issuing_entity or "",
        })
    return rows


# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/types")
async def get_report_types(current_user: User = Depends(get_current_user)):
    """Obtener tipos de reportes disponibles."""
    return [
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
            "description": "Estado de certificaciones del personal con alertas de vencimiento",
            "formats": ["excel", "pdf"],
        },
        {
            "id": "summary",
            "name": "Resumen Ejecutivo",
            "description": "KPIs principales, cumplimiento general y alertas del periodo",
            "formats": ["pdf"],
        },
    ]


@router.get("/preview/{report_type}")
async def preview_report(
    report_type: str,
    year: int = Query(..., ge=2020, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Vista previa de datos del reporte (JSON)."""
    org_id = current_user.organization_id

    if report_type == "compliance":
        rows, _ = _get_compliance_data(db, year, month or datetime.now().month, org_id, user_id)
        return {"type": "compliance", "period": f"{MONTH_NAMES[month or datetime.now().month]} {year}", "total_rows": len(rows), "data": rows}

    elif report_type == "emergencies":
        rows = _get_emergencies_data(db, year, month, org_id)
        return {"type": "emergencies", "period": f"{MONTH_NAMES[month] if month else 'Anual'} {year}", "total_rows": len(rows), "data": rows}

    elif report_type == "equipment":
        rows = _get_equipment_data(db, org_id)
        return {"type": "equipment", "total_rows": len(rows), "data": rows}

    elif report_type == "certifications":
        rows = _get_certifications_data(db, org_id)
        return {"type": "certifications", "total_rows": len(rows), "data": rows}

    return {"error": "Tipo de reporte no valido"}


@router.get("/export/{report_type}")
async def export_report(
    report_type: str,
    format: str = Query("excel", regex="^(excel|pdf)$"),
    year: int = Query(..., ge=2020, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exportar reporte en Excel o PDF."""
    org_id = current_user.organization_id
    period = f"{MONTH_NAMES[month] if month else 'Anual'} {year}"

    if format == "excel":
        return _export_excel(db, report_type, year, month, org_id, user_id, period)
    else:
        return _export_pdf(db, report_type, year, month, org_id, user_id, period)


def _export_excel(db, report_type, year, month, org_id, user_id, period):
    """Generar archivo Excel."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Dependencia openpyxl no instalada. Ejecute: pip install openpyxl"}
        )

    wb = Workbook()
    ws = wb.active

    # Estilos
    header_font = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    title_font = Font(name='Calibri', bold=True, size=14, color='1F4E79')
    subtitle_font = Font(name='Calibri', size=11, color='666666')
    border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9'),
    )

    # Titulo
    ws.merge_cells('A1:F1')
    ws['A1'] = f"Gestion GAE - Reporte de {report_type.title()}"
    ws['A1'].font = title_font
    ws['A2'] = f"Periodo: {period} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws['A2'].font = subtitle_font

    row_start = 4

    if report_type == "compliance":
        ws.title = "Cumplimiento"
        headers = ["Usuario", "Categoria", "Actividad", "C1 Plan", "C1 Ejec", "C2 Plan", "C2 Ejec",
                   "C3 Plan", "C3 Ejec", "C4 Plan", "C4 Ejec", "Total Plan", "Total Ejec", "Cumplimiento %"]
        rows, _ = _get_compliance_data(db, year, month or datetime.now().month, org_id, user_id)
        data_keys = ["usuario", "categoria", "actividad", "ciclo_1_plan", "ciclo_1_ejec",
                     "ciclo_2_plan", "ciclo_2_ejec", "ciclo_3_plan", "ciclo_3_ejec",
                     "ciclo_4_plan", "ciclo_4_ejec", "total_planeado", "total_ejecutado", "cumplimiento"]

    elif report_type == "emergencies":
        ws.title = "Emergencias"
        headers = ["Codigo", "Tipo", "Fecha", "Ubicacion", "Descripcion", "Severidad", "T. Respuesta (min)", "Estado", "Reportado por"]
        rows = _get_emergencies_data(db, year, month, org_id)
        data_keys = ["codigo", "tipo", "fecha", "ubicacion", "descripcion", "severidad", "tiempo_respuesta_min", "estado", "reportado_por"]

    elif report_type == "equipment":
        ws.title = "Equipos"
        headers = ["Codigo", "Nombre", "Categoria", "Marca", "Modelo", "Serie", "Estado", "Ubicacion", "Prox. Mantenimiento"]
        rows = _get_equipment_data(db, org_id)
        data_keys = ["codigo", "nombre", "categoria", "marca", "modelo", "serie", "estado", "ubicacion", "proximo_mantenimiento"]

    elif report_type == "certifications":
        ws.title = "Certificaciones"
        headers = ["Usuario", "Certificacion", "Fecha Emision", "Fecha Vencimiento", "Dias Restantes", "Estado", "Entidad"]
        rows = _get_certifications_data(db, org_id)
        data_keys = ["usuario", "certificacion", "fecha_emision", "fecha_vencimiento", "dias_restantes", "estado", "entidad"]
    else:
        headers = []
        rows = []
        data_keys = []

    # Escribir headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row_start, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border

    # Escribir datos
    for row_idx, row_data in enumerate(rows, row_start + 1):
        for col_idx, key in enumerate(data_keys, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=row_data.get(key, ""))
            cell.border = border
            cell.alignment = Alignment(vertical='center')

    # Ajustar anchos de columna
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_length + 4, 40)

    # Generar archivo
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"reporte_{report_type}_{period.replace(' ', '_')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _export_pdf(db, report_type, year, month, org_id, user_id, period):
    """Generar archivo PDF con formato tabular simple."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Dependencia reportlab no instalada. Ejecute: pip install reportlab"}
        )

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []

    # Titulo
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#1F4E79'))
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.gray)

    elements.append(Paragraph(f"Gestion GAE - Reporte de {report_type.title()}", title_style))
    elements.append(Paragraph(f"Periodo: {period} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 20))

    # Obtener datos segun tipo
    if report_type == "compliance":
        headers = ["Usuario", "Categoria", "Actividad", "Plan", "Ejec", "Cumpl. %"]
        rows, _ = _get_compliance_data(db, year, month or datetime.now().month, org_id, user_id)
        table_data = [headers]
        for r in rows:
            table_data.append([r["usuario"], r["categoria"], r["actividad"],
                             r["total_planeado"], r["total_ejecutado"], f"{r['cumplimiento']}%"])

    elif report_type == "emergencies":
        headers = ["Codigo", "Tipo", "Fecha", "Severidad", "T. Resp.", "Estado"]
        rows = _get_emergencies_data(db, year, month, org_id)
        table_data = [headers]
        for r in rows:
            table_data.append([r["codigo"], r["tipo"], r["fecha"],
                             r["severidad"], f"{r['tiempo_respuesta_min']} min", r["estado"]])

    elif report_type == "equipment":
        headers = ["Codigo", "Nombre", "Categoria", "Estado", "Ubicacion", "Prox. Mtto"]
        rows = _get_equipment_data(db, org_id)
        table_data = [headers]
        for r in rows:
            table_data.append([r["codigo"], r["nombre"], r["categoria"],
                             r["estado"], r["ubicacion"], r["proximo_mantenimiento"]])

    elif report_type == "certifications":
        headers = ["Usuario", "Certificacion", "Vencimiento", "Dias Rest.", "Estado", "Entidad"]
        rows = _get_certifications_data(db, org_id)
        table_data = [headers]
        for r in rows:
            table_data.append([r["usuario"], r["certificacion"], r["fecha_vencimiento"],
                             r["dias_restantes"], r["estado"], r["entidad"]])

    elif report_type == "summary":
        # Resumen ejecutivo
        m = month or datetime.now().month
        compliance_rows, plans = _get_compliance_data(db, year, m, org_id)
        total_planned = sum(r["total_planeado"] for r in compliance_rows)
        total_executed = sum(r["total_ejecutado"] for r in compliance_rows)
        overall = (total_executed / total_planned * 100) if total_planned > 0 else 0

        accidents = db.query(Accident).filter(
            extract('year', Accident.accident_date) == year,
            extract('month', Accident.accident_date) == m
        ).count()

        emg_q = db.query(Emergency).filter(
            extract('year', Emergency.reported_at) == year,
            extract('month', Emergency.reported_at) == m
        )
        if org_id is not None:
            emg_q = emg_q.filter(Emergency.organization_id == org_id)
        emergencies_count = emg_q.count()

        headers = ["Indicador", "Valor"]
        table_data = [
            headers,
            ["Periodo", f"{MONTH_NAMES[m]} {year}"],
            ["Accidentes", str(accidents)],
            ["Emergencias Atendidas", str(emergencies_count)],
            ["Total Actividades Planeadas", str(total_planned)],
            ["Total Actividades Ejecutadas", str(total_executed)],
            ["Cumplimiento General", f"{overall:.1f}%"],
            ["Usuarios con Plan", str(len(plans))],
        ]
    else:
        table_data = [["No hay datos"]]

    # Crear tabla
    if len(table_data) > 1:
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9D9D9')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Total de registros: {len(table_data) - 1}", styles['Normal']))

    doc.build(elements)
    output.seek(0)

    filename = f"reporte_{report_type}_{period.replace(' ', '_')}.pdf"
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
