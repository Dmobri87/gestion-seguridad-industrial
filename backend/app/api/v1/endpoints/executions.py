import os
import re
import uuid
import shutil
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, ensure_org_access
from app.core.audit import log_audit
from app.models.user import User, UserRole
from app.models.planning import PlannedActivity, MonthlyPlan
from app.models.execution import ActivityExecution, ExecutionFile, ExecutionHistory, ExecutionStatus, ApprovalStatus
from app.schemas.execution import (
    ActivityExecutionResponse, ActivityExecutionCreateV1, ActivityExecutionUpdateV1,
    ActivityExecutionWithDetails, ExecutionFileResponse, ExecutionFileCreate,
    ExecutionApprovalRequest, ExecutionApprovalResponse, ExecutionStats
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


@router.get("/", response_model=List[ActivityExecutionWithDetails])
async def get_executions(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    approval_status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar ejecuciones con filtros."""
    query = db.query(ActivityExecution).options(
        joinedload(ActivityExecution.user),
        joinedload(ActivityExecution.planned_activity).joinedload(PlannedActivity.activity_template)
    )

    # Filtrar por organización
    if current_user.organization_id:
        query = query.filter(ActivityExecution.organization_id == current_user.organization_id)

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
    if current_user.organization_id and execution_data.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para registrar ejecuciones en esta organización"
        )

    # Verificar que la actividad planeada existe
    planned = db.query(PlannedActivity).filter(
        PlannedActivity.id == execution_data.planned_activity_id
    ).first()

    if not planned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad planeada no encontrada"
        )
    ensure_org_access(current_user, planned.monthly_plan, "plan")

    # Verificar que el usuario exista y pertenezca a la organización
    target_user_id = execution_data.user_id or current_user.id
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    ensure_org_access(current_user, target_user, "usuario")

    # Crear ejecución
    execution = ActivityExecution(
        planned_activity_id=execution_data.planned_activity_id,
        user_id=target_user_id,
        execution_date=execution_data.execution_date,
        cycle_number=execution_data.cycle_number,
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

    db.add(execution)

    # Actualizar contadores
    _update_execution_counts(planned, execution_data.cycle_number, execution_data.quantity)
    _recalculate_activity_compliance(planned)

    # Actualizar plan
    plan = planned.monthly_plan
    plan.total_executed += execution_data.quantity
    if plan.total_planned > 0:
        plan.compliance_percentage = (plan.total_executed / plan.total_planned) * 100

    db.commit()
    db.refresh(execution)

    log_audit(
        db=None,
        action="EXECUTION_CREATED",
        resource_type="executions",
        resource_id=execution.id,
        current_user=current_user,
        request=None,
        description="Ejecución registrada",
    )

    return execution


def _update_execution_counts(planned: PlannedActivity, cycle: int, quantity: int):
    """Actualizar contadores de ejecución por ciclo."""
    if cycle == 1:
        planned.cycle_1_executed += quantity
    elif cycle == 2:
        planned.cycle_2_executed += quantity
    elif cycle == 3:
        planned.cycle_3_executed += quantity
    elif cycle == 4:
        planned.cycle_4_executed += quantity
    planned.total_executed += quantity


def _recalculate_activity_compliance(planned: PlannedActivity):
    """Recalcular compliance de una actividad."""
    if planned.total_planned > 0:
        planned.compliance_percentage = (planned.total_executed / planned.total_planned) * 100


@router.get("/my-today")
async def get_my_today_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener actividades pendientes del usuario para hoy."""
    today = date.today()

    # Obtener plan actual del usuario
    plan = db.query(MonthlyPlan).filter(
        and_(
            MonthlyPlan.user_id == current_user.id,
            MonthlyPlan.year == today.year,
            MonthlyPlan.month == today.month
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

    result = []
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
                "requires_evidence": pa.activity_template.requires_evidence if pa.activity_template else False
            })

    return {"activities": result, "plan_id": plan.id}


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
    ensure_org_access(current_user, execution, "ejecución")

    execution.approval_status = ApprovalStatus.APPROVED.value if approval_data.approved else ApprovalStatus.REJECTED.value
    execution.approved_by = current_user.id
    execution.approved_at = datetime.utcnow()
    if not approval_data.approved:
        execution.rejection_reason = approval_data.rejection_reason

    db.commit()

    log_audit(
        db=None,
        action="EXECUTION_APPROVED" if approval_data.approved else "EXECUTION_REJECTED",
        resource_type="executions",
        resource_id=execution.id,
        current_user=current_user,
        request=None,
        description="Aprobación de ejecución",
    )

    return ExecutionApprovalResponse(
        execution_id=execution.id,
        approval_status=execution.approval_status,
        approved_by=execution.approved_by,
        approved_at=execution.approved_at,
        rejection_reason=execution.rejection_reason
    )


@router.get("/stats", response_model=ExecutionStats)
async def get_execution_stats(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de ejecuciones."""
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
    ensure_org_access(current_user, execution, "ejecución")

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
    log_audit(
        db=None,
        action="EVIDENCE_UPLOADED",
        resource_type="execution_files",
        resource_id=db_file.id,
        current_user=current_user,
        request=None,
        description="Archivo de evidencia subido",
    )
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
    ensure_org_access(current_user, execution, "ejecución")

    files = db.query(ExecutionFile).filter(
        ExecutionFile.execution_id == execution_id
    ).order_by(ExecutionFile.created_at.desc()).all()

    return files


@router.get("/files/{file_id}/download")
async def download_execution_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Descargar un archivo de evidencia con autorización."""
    db_file = db.query(ExecutionFile).filter(ExecutionFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    execution = db.query(ActivityExecution).filter(ActivityExecution.id == db_file.execution_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")
    ensure_org_access(current_user, execution, "ejecución")

    # Permisos: dueño de la ejecución o coordinador/admin
    if current_user.id != execution.user_id and current_user.role not in [
        UserRole.ADMIN.value,
        UserRole.COORDINATOR.value,
    ]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para descargar este archivo")

    if not db_file.file_url.startswith("/uploads/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ruta de archivo inválida")

    relative_path = db_file.file_url.replace("/uploads/", "", 1)
    file_path = os.path.join(UPLOAD_DIR, relative_path)

    real_upload = os.path.realpath(UPLOAD_DIR)
    real_file = os.path.realpath(file_path)
    if not real_file.startswith(real_upload):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ruta de archivo inválida")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado en el servidor")

    return FileResponse(
        path=file_path,
        media_type=db_file.file_type or "application/octet-stream",
        filename=db_file.file_name
    )


@router.delete("/{execution_id}/files/{file_id}")
async def delete_execution_file(
    execution_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un archivo de evidencia."""
    db_file = db.query(ExecutionFile).filter(
        ExecutionFile.id == file_id,
        ExecutionFile.execution_id == execution_id
    ).first()

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )

    execution = db.query(ActivityExecution).filter(ActivityExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejecución no encontrada"
        )
    ensure_org_access(current_user, execution, "ejecución")

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

    log_audit(
        db=None,
        action="EVIDENCE_DELETED",
        resource_type="execution_files",
        resource_id=db_file.id,
        current_user=current_user,
        request=None,
        description="Archivo de evidencia eliminado",
    )

    return {"message": "Archivo eliminado correctamente"}
