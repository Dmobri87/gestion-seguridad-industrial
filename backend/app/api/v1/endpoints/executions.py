import os
import re
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.planning import PlannedActivity, MonthlyPlan
from app.models.execution import ActivityExecution, ExecutionFile, ExecutionHistory, ExecutionStatus, ApprovalStatus
from app.services.compliance_service import recalculate_plan_compliance
from app.schemas.execution import (
    ActivityExecutionResponse, ActivityExecutionCreateV1,
    ActivityExecutionWithDetails, ExecutionFileResponse,
    ExecutionApprovalRequest, ExecutionApprovalResponse, ExecutionStats,
    ExecutionCorrectionRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuración de uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".mp4", ".mov", ".avi"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Magic bytes para validación de tipo de archivo
MAGIC_BYTES = {
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".gif": [b"GIF87a", b"GIF89a"],
    ".bmp": [b"BM"],
    ".webp": [b"RIFF"],
    ".pdf": [b"%PDF"],
    ".doc": [b"\xd0\xcf\x11\xe0"],
    ".docx": [b"PK\x03\x04"],
    ".xls": [b"\xd0\xcf\x11\xe0"],
    ".xlsx": [b"PK\x03\x04"],
    ".mp4": [b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x1cftyp", b"\x00\x00\x00\x20ftyp"],
    ".mov": [b"\x00\x00\x00\x14ftyp"],
    ".avi": [b"RIFF"],
}


def _sanitize_filename(filename: str) -> str:
    """Sanitiza el nombre de archivo eliminando caracteres peligrosos."""
    # Extraer solo el nombre, sin rutas
    name = os.path.basename(filename)
    # Eliminar caracteres no alfanuméricos excepto punto, guion y guion bajo
    name = re.sub(r'[^\w\-.]', '_', name)
    # Eliminar doble punto (path traversal)
    name = name.replace('..', '_')
    return name[:255]  # Limitar longitud


def _validate_magic_bytes(content: bytes, extension: str) -> bool:
    """Valida que los primeros bytes del archivo coincidan con la extensión declarada."""
    signatures = MAGIC_BYTES.get(extension)
    if not signatures:
        return True  # Si no hay firma conocida, aceptar
    return any(content.startswith(sig) for sig in signatures)


def _apply_role_filter(query, current_user: User, db: Session):
    """
    Aplica filtrado por rol a una query de ActivityExecution.
    - TAE/PSE: solo sus propias ejecuciones
    - Coordinador: ejecuciones de TAEs cuyos planes creó él
    - Supervisor: ejecuciones de TAEs subordinados (supervisor_id)
    - Administrador: sin filtro adicional
    """
    role = current_user.role

    if role in (UserRole.TAE.value, UserRole.PSE.value):
        query = query.filter(ActivityExecution.user_id == current_user.id)

    elif role == UserRole.COORDINATOR.value:
        # TAEs cuyos planes fueron creados por este coordinador
        from sqlalchemy import select
        subordinate_ids = (
            select(MonthlyPlan.user_id)
            .where(MonthlyPlan.created_by == current_user.id)
            .distinct()
        )
        query = query.filter(ActivityExecution.user_id.in_(subordinate_ids))

    elif role == UserRole.SUPERVISOR.value:
        # TAEs que reportan a este supervisor
        from sqlalchemy import select
        subordinate_ids = (
            select(User.id)
            .where(User.supervisor_id == current_user.id)
        )
        query = query.filter(ActivityExecution.user_id.in_(subordinate_ids))

    # Administrador: sin filtro adicional

    return query


def _enforce_execution_file_access(execution: ActivityExecution, current_user: User):
    """Restringe acceso a evidencias para roles operativos al dueño de la ejecución."""
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        if execution.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a los archivos de esta ejecución"
            )


@router.get("/", response_model=List[ActivityExecutionWithDetails])
async def get_executions(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    approval_status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar ejecuciones con filtros. Resultados filtrados según rol del usuario."""
    query = db.query(ActivityExecution).options(
        joinedload(ActivityExecution.user),
        joinedload(ActivityExecution.planned_activity).joinedload(PlannedActivity.activity_template)
    )

    # Filtrar por organización
    if current_user.organization_id:
        query = query.filter(ActivityExecution.organization_id == current_user.organization_id)

    # Filtrado por rol
    query = _apply_role_filter(query, current_user, db)

    # Fix C-1: Validate user_id query param against the current user's accessible scope
    if user_id is not None:
        role = current_user.role
        if role in (UserRole.TAE.value, UserRole.PSE.value):
            # TAE/PSE can only query their own executions
            if user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para ver ejecuciones de otro usuario"
                )
        elif role == UserRole.COORDINATOR.value:
            # Coordinator can only query users whose plans they created
            from sqlalchemy import select as sa_select
            allowed_ids = db.execute(
                sa_select(MonthlyPlan.user_id)
                .where(MonthlyPlan.created_by == current_user.id)
                .distinct()
            ).scalars().all()
            if user_id not in allowed_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes autoridad sobre el usuario indicado"
                )
        # Admin/Supervisor: allow any user_id within org (no extra check needed)

    # Filtro por fecha
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    query = query.filter(
        and_(
            ActivityExecution.execution_date >= start_date,
            ActivityExecution.execution_date < end_date
        )
    )

    if user_id:
        query = query.filter(ActivityExecution.user_id == user_id)
    if status:
        query = query.filter(ActivityExecution.status == status)
    if approval_status:
        query = query.filter(ActivityExecution.approval_status == approval_status)

    executions = query.order_by(ActivityExecution.execution_date.desc()).offset(skip).limit(limit).all()

    result = []
    for ex in executions:
        ex_dict = {
            **ActivityExecutionResponse.model_validate(ex).model_dump(),
            "user_name": ex.user.full_name if ex.user else "",
            "activity_name": ex.planned_activity.activity_template.name if ex.planned_activity and ex.planned_activity.activity_template else "",
            "activity_code": ex.planned_activity.activity_template.code if ex.planned_activity and ex.planned_activity.activity_template else "",
            "category_name": "",
            "files_count": len(ex.files) if ex.files else 0
        }
        result.append(ActivityExecutionWithDetails(**ex_dict))

    return result


@router.post("/", response_model=ActivityExecutionResponse)
async def create_execution(
    execution_data: ActivityExecutionCreateV1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar nueva ejecución de actividad."""
    # Verificar que la actividad planeada existe
    planned = db.query(PlannedActivity).filter(
        PlannedActivity.id == execution_data.planned_activity_id
    ).first()

    if not planned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad planeada no encontrada"
        )

    # Fix H-3: For TAE/PSE, always force user_id to current user — ignore any client-supplied value.
    # Only Admin/Coordinator/Supervisor are allowed to submit on behalf of another user.
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        resolved_user_id = current_user.id
    else:
        resolved_user_id = execution_data.user_id or current_user.id

    # Crear ejecución
    cycle_number = max(1, min(execution_data.cycle_number, 3))
    execution = ActivityExecution(
        planned_activity_id=execution_data.planned_activity_id,
        user_id=resolved_user_id,
        execution_date=execution_data.execution_date,
        cycle_number=cycle_number,
        status=execution_data.status,
        observation=execution_data.observation,
        novelty_description=execution_data.novelty_description,
        location=execution_data.location,
        quantity=execution_data.quantity,
        organization_id=execution_data.organization_id or current_user.organization_id,
        approval_status=ApprovalStatus.PENDING.value,
        is_editable=True,
        edit_deadline=datetime.utcnow() + timedelta(hours=24)
    )

    # Capturar plan_id ANTES del commit (después del commit, 'planned' queda expirado)
    monthly_plan_id = planned.monthly_plan_id

    db.add(execution)
    db.commit()
    db.refresh(execution)

    try:
        recalculate_plan_compliance(db, monthly_plan_id)
    except Exception as e:
        logger.error(f"recalculate_plan_compliance falló para plan {monthly_plan_id}: {e}")

    return execution


def _update_execution_counts(planned: PlannedActivity, cycle: int, quantity: int):
    """Actualizar contadores de ejecución por ciclo."""
    if cycle == 1:
        planned.cycle_1_executed += quantity
    elif cycle == 2:
        planned.cycle_2_executed += quantity
    elif cycle == 3:
        planned.cycle_3_executed += quantity
    else:
        pass
    planned.total_executed += quantity


def _recalculate_activity_compliance(planned: PlannedActivity):
    """Recalcular compliance de una actividad."""
    if planned.total_planned > 0:
        planned.compliance_percentage = (planned.total_executed / planned.total_planned) * 100


@router.get("/my-today")
async def get_my_today_activities(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener actividades pendientes del usuario para el mes/año indicado."""
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month

    # Obtener plan del usuario para el mes indicado (cualquier estado)
    plan = db.query(MonthlyPlan).filter(
        and_(
            MonthlyPlan.user_id == current_user.id,
            MonthlyPlan.year == target_year,
            MonthlyPlan.month == target_month
        )
    ).first()

    if not plan:
        return {"activities": [], "message": "No tienes plan para este mes"}

    # Obtener actividades planeadas con detalle
    planned_activities = db.query(PlannedActivity).options(
        joinedload(PlannedActivity.activity_template)
    ).filter(
        PlannedActivity.monthly_plan_id == plan.id,
        PlannedActivity.is_active == True
    ).all()

    # Contar ejecuciones reales desde BD (no los campos cacheados que pueden estar desactualizados)
    activity_ids = [pa.id for pa in planned_activities]
    exec_counts: dict = {}
    if activity_ids:
        from sqlalchemy import func as sqlfunc
        rows = (
            db.query(
                ActivityExecution.planned_activity_id,
                sqlfunc.coalesce(
                    sqlfunc.sum(sqlfunc.coalesce(ActivityExecution.quantity, 1)), 0
                ).label("total_qty"),
            )
            .filter(
                ActivityExecution.planned_activity_id.in_(activity_ids),
                ActivityExecution.approval_status != ApprovalStatus.REJECTED.value,
            )
            .group_by(ActivityExecution.planned_activity_id)
            .all()
        )
        exec_counts = {row.planned_activity_id: int(row.total_qty) for row in rows}

    result = []
    for pa in planned_activities:
        total_planned = (
            (pa.cycle_1_planned or 0)
            + (pa.cycle_2_planned or 0)
            + (pa.cycle_3_planned or 0)
        )
        if total_planned == 0:
            continue
        total_executed = exec_counts.get(pa.id, 0)
        pending = total_planned - total_executed
        if pending > 0:
            compliance = round((total_executed / total_planned) * 100, 2)
            result.append({
                "planned_activity_id": pa.id,
                "activity_name": pa.activity_template.name if pa.activity_template else "",
                "activity_code": pa.activity_template.code if pa.activity_template else "",
                "total_planned": total_planned,
                "total_executed": total_executed,
                "pending": pending,
                "compliance_percentage": compliance,
                "requires_evidence": pa.requires_evidence,
            })

    return {"activities": result, "plan_id": plan.id}


@router.get("/my-pending-all")
async def get_all_my_pending_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener TODAS las actividades pendientes del usuario en todos sus planes."""
    plans = db.query(MonthlyPlan).filter(
        MonthlyPlan.user_id == current_user.id,
        MonthlyPlan.status.in_(["Borrador", "Aprobado", "En Progreso"])
    ).all()

    result = []
    for plan in plans:
        planned_activities = db.query(PlannedActivity).options(
            joinedload(PlannedActivity.activity_template)
        ).filter(
            PlannedActivity.monthly_plan_id == plan.id,
            PlannedActivity.is_active == True
        ).all()

        for pa in planned_activities:
            pending = pa.total_planned - pa.total_executed
            if pending > 0:
                result.append({
                    "planned_activity_id": pa.id,
                    "activity_name": pa.activity_template.name if pa.activity_template else "",
                    "activity_code": pa.activity_template.code if pa.activity_template else "",
                    "total_planned": pa.total_planned,
                    "total_executed": pa.total_executed,
                    "pending": pending,
                    "compliance_percentage": pa.compliance_percentage,
                    "requires_evidence": pa.requires_evidence,
                    "month": plan.month,
                    "year": plan.year,
                })

    return {"activities": result, "total_pending": len(result)}


@router.get("/stats", response_model=ExecutionStats)
async def get_execution_stats(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de ejecuciones. Filtradas según rol del usuario."""
    start_date = date(year, month, 1)
    end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)

    query = db.query(ActivityExecution).filter(
        and_(
            ActivityExecution.execution_date >= start_date,
            ActivityExecution.execution_date < end_date
        )
    )

    if current_user.organization_id:
        query = query.filter(ActivityExecution.organization_id == current_user.organization_id)

    # Filtrado por rol
    query = _apply_role_filter(query, current_user, db)

    if user_id:
        query = query.filter(ActivityExecution.user_id == user_id)

    executions = query.all()

    return ExecutionStats(
        total_executions=len(executions),
        completed=sum(1 for e in executions if e.status == ExecutionStatus.COMPLETED.value),
        pending=sum(1 for e in executions if e.status == ExecutionStatus.PENDING.value),
        with_novelty=sum(1 for e in executions if e.status == ExecutionStatus.WITH_NOVELTY.value),
        pending_approval=sum(1 for e in executions if e.approval_status == ApprovalStatus.PENDING.value),
        approved=sum(1 for e in executions if e.approval_status == ApprovalStatus.APPROVED.value),
        rejected=sum(1 for e in executions if e.approval_status == ApprovalStatus.REJECTED.value)
    )


@router.get("/files/serve/{filename}")
async def serve_evidence_file(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Servir archivo de evidencia con autenticación."""
    if not re.match(r'^[a-f0-9]{32}\.[a-z0-9]+$', filename):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    file_path = os.path.join(UPLOAD_DIR, "evidences", filename)
    real_upload = os.path.realpath(os.path.join(UPLOAD_DIR, "evidences"))
    real_file = os.path.realpath(file_path)

    if not real_file.startswith(real_upload):
        raise HTTPException(status_code=400, detail="Ruta inválida")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    db_file = db.query(ExecutionFile).filter(
        ExecutionFile.file_url == f"/uploads/evidences/{filename}"
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    execution = db.query(ActivityExecution).filter(
        ActivityExecution.id == db_file.execution_id
    ).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Ejecución no encontrada")
    _enforce_execution_file_access(execution, current_user)

    return FileResponse(file_path)


@router.post("/{execution_id}/approve", response_model=ExecutionApprovalResponse)
async def approve_execution(
    execution_id: int,
    approval_data: ExecutionApprovalRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value])),
    db: Session = Depends(get_db)
):
    """Aprobar o rechazar una ejecución."""
    execution = db.query(ActivityExecution).filter(ActivityExecution.id == execution_id).first()

    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")

    if approval_data.approved and execution.planned_activity and execution.planned_activity.requires_evidence:
        files_count = db.query(ExecutionFile.id).filter(
            ExecutionFile.execution_id == execution.id
        ).count()
        if files_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta actividad requiere evidencia antes de aprobarse"
            )

    execution.approval_status = ApprovalStatus.APPROVED.value if approval_data.approved else ApprovalStatus.REJECTED.value
    execution.approved_by = current_user.id
    execution.approved_at = datetime.utcnow()
    if not approval_data.approved:
        execution.rejection_reason = approval_data.rejection_reason

    db.commit()
    if execution.planned_activity:
        recalculate_plan_compliance(db, execution.planned_activity.monthly_plan_id)

    return ExecutionApprovalResponse(
        execution_id=execution.id,
        approval_status=execution.approval_status,
        approved_by=execution.approved_by,
        approved_at=execution.approved_at,
        rejection_reason=execution.rejection_reason
    )


@router.put("/{execution_id}/correct", response_model=ActivityExecutionResponse)
async def correct_execution(
    execution_id: int,
    correction_data: ExecutionCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Corregir y reenviar una ejecución rechazada.
    Solo el TAE que creó la ejecución puede corregirla.
    """
    execution = db.query(ActivityExecution).filter(
        ActivityExecution.id == execution_id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejecución no encontrada"
        )
    _enforce_execution_file_access(execution, current_user)

    # Solo el creador puede corregir
    if execution.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el TAE que creó la ejecución puede corregirla"
        )

    # Solo se pueden corregir ejecuciones rechazadas
    if execution.approval_status != ApprovalStatus.REJECTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden corregir ejecuciones con estado Rechazado"
        )

    # Aplicar correcciones
    changes = []
    for field in ("observation", "novelty_description", "status", "location", "quantity"):
        new_value = getattr(correction_data, field, None)
        if new_value is not None:
            old_value = getattr(execution, field)
            setattr(execution, field, new_value)
            changes.append(f"{field}: {old_value} -> {new_value}")

    # Reenviar para aprobación
    execution.approval_status = ApprovalStatus.PENDING.value
    execution.rejection_reason = None
    execution.is_editable = True
    execution.approved_by = None
    execution.approved_at = None

    # Registrar en historial
    history_entry = ExecutionHistory(
        execution_id=execution.id,
        action="CORRECT",
        field_changed=", ".join(changes) if changes else "resubmit",
        old_value=ApprovalStatus.REJECTED.value,
        new_value=ApprovalStatus.PENDING.value,
        changed_by=current_user.id,
        reason="Corrección y reenvío de ejecución rechazada",
    )
    db.add(history_entry)

    db.commit()
    db.refresh(execution)
    if execution.planned_activity:
        recalculate_plan_compliance(db, execution.planned_activity.monthly_plan_id)

    logger.info(
        "Ejecución %s corregida y reenviada por usuario %s",
        execution_id, current_user.email,
    )

    return execution


# ==========================================
# ARCHIVOS / EVIDENCIAS
# ==========================================

@router.post("/{execution_id}/files", response_model=ExecutionFileResponse)
async def upload_execution_file(
    execution_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subir archivo de evidencia a una ejecución.
    Soporta imágenes, PDFs, documentos y videos (máx. 10MB).
    """
    # Verificar que la ejecución existe
    execution = db.query(ActivityExecution).filter(
        ActivityExecution.id == execution_id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejecución no encontrada"
        )

    # Fix H-4: Enforce access control before any file processing
    _enforce_execution_file_access(execution, current_user)

    # Sanitizar y validar nombre de archivo
    original_filename = _sanitize_filename(file.filename or "archivo")
    file_ext = os.path.splitext(original_filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Extensiones válidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Leer archivo con límite de tamaño (streaming)
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        chunks.append(chunk)
    content = b"".join(chunks)
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío"
        )

    # Validar magic bytes
    if not _validate_magic_bytes(content, file_ext):
        logger.warning(
            "Archivo rechazado por magic bytes: ext=%s, user=%s",
            file_ext, current_user.email
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido del archivo no coincide con la extensión declarada"
        )

    # Generar nombre único (nunca usar nombre original del usuario)
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    evidences_dir = os.path.join(UPLOAD_DIR, "evidences")
    os.makedirs(evidences_dir, exist_ok=True)
    file_path = os.path.join(evidences_dir, unique_name)

    # Verificar que la ruta final está dentro del directorio de uploads (path traversal)
    real_upload = os.path.realpath(UPLOAD_DIR)
    real_dest = os.path.realpath(file_path)
    if not real_dest.startswith(real_upload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ruta de archivo no válida"
        )

    # Guardar archivo
    with open(file_path, "wb") as f:
        f.write(content)

    # Determinar tipo MIME
    mime_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".bmp": "image/bmp", ".webp": "image/webp",
        ".pdf": "application/pdf",
        ".doc": "application/msword", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".mp4": "video/mp4", ".mov": "video/quicktime", ".avi": "video/x-msvideo",
    }
    file_type = mime_types.get(file_ext, "application/octet-stream")

    # Contar archivos existentes para marcar el primero como primary
    existing_count = db.query(ExecutionFile).filter(
        ExecutionFile.execution_id == execution_id
    ).count()

    # Crear registro en BD
    db_file = ExecutionFile(
        execution_id=execution_id,
        file_name=original_filename,
        file_type=file_type,
        file_size=file_size,
        file_url=f"/uploads/evidences/{unique_name}",
        description=description,
        is_primary=(existing_count == 0),
        uploaded_by=current_user.id,
    )

    try:
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
    except Exception:
        db.rollback()
        # Limpiar archivo huérfano si falla el commit
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.exception("Error guardando archivo de evidencia para ejecución: %s", execution_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al guardar el archivo"
        )

    logger.info("Archivo subido: %s para ejecución %s por %s", unique_name, execution_id, current_user.email)
    return db_file


@router.get("/{execution_id}/files", response_model=List[ExecutionFileResponse])
async def get_execution_files(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar archivos de evidencia de una ejecución."""
    execution = db.query(ActivityExecution).filter(
        ActivityExecution.id == execution_id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejecución no encontrada"
        )
    _enforce_execution_file_access(execution, current_user)

    files = db.query(ExecutionFile).filter(
        ExecutionFile.execution_id == execution_id
    ).order_by(ExecutionFile.created_at.desc()).all()

    return files


@router.delete("/{execution_id}/files/{file_id}")
async def delete_execution_file(
    execution_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un archivo de evidencia."""
    execution = db.query(ActivityExecution).filter(
        ActivityExecution.id == execution_id
    ).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejecución no encontrada"
        )
    _enforce_execution_file_access(execution, current_user)

    db_file = db.query(ExecutionFile).filter(
        ExecutionFile.id == file_id,
        ExecutionFile.execution_id == execution_id
    ).first()

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )

    # Solo el que subió o un admin puede eliminar
    if db_file.uploaded_by != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este archivo"
        )

    # Eliminar archivo físico
    relative_path = db_file.file_url.replace("/uploads/", "", 1)
    file_path = os.path.join(UPLOAD_DIR, relative_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(db_file)
    db.commit()

    return {"message": "Archivo eliminado correctamente"}
