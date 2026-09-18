import json
import logging
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.compliance import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS = {
    "password",
    "hashed_password",
    "otp_code",
    "otp_expires_at",
    "otp_attempts",
    "two_factor_secret",
}


def _sanitize(data: Optional[dict]) -> Optional[str]:
    if not data:
        return None
    safe = {}
    for k, v in data.items():
        if k in SENSITIVE_FIELDS:
            safe[k] = "***"
        else:
            safe[k] = v
    try:
        return json.dumps(safe, ensure_ascii=False, default=str)
    except Exception:
        return None


def log_audit(
    db: Optional[Session],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    current_user: Optional[User] = None,
    request: Optional[Request] = None,
    description: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
):
    """Registra evento de auditoría sin afectar la transacción principal."""
    audit_db = None
    try:
        audit_db = db or SessionLocal()
        audit = AuditLog(
            user_id=current_user.id if current_user else None,
            user_email=current_user.email if current_user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            old_values=_sanitize(old_values),
            new_values=_sanitize(new_values),
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            organization_id=current_user.organization_id if current_user else None,
        )
        audit_db.add(audit)
        audit_db.commit()
    except Exception:
        if audit_db:
            audit_db.rollback()
        logger.exception("Error registrando auditoría")
    finally:
        if audit_db and audit_db is not db:
            audit_db.close()
