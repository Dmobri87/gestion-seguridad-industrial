from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.certification import Notification, UserCertification
from app.models.user import User, UserRole

router = APIRouter()


def _priority_for_days(days_left: int) -> str:
    if days_left < 0:
        return "critical"
    if days_left <= 7:
        return "urgent"
    return "warning"


def _type_for_priority(priority: str) -> str:
    if priority == "critical":
        return "error"
    if priority in {"urgent", "warning"}:
        return "warning"
    return "info"


def _build_title(days_left: int, cert_name: str) -> str:
    if days_left < 0:
        return f"Certificacion vencida: {cert_name}"
    return f"Certificacion por vencer: {cert_name}"


def _build_message(days_left: int, cert_name: str, expiry_date: date) -> str:
    if days_left < 0:
        return f"La certificacion {cert_name} vencio el {expiry_date.strftime('%d/%m/%Y')}."
    return (
        f"La certificacion {cert_name} vence en {days_left} dias "
        f"({expiry_date.strftime('%d/%m/%Y')})."
    )


@router.get("/check-expirations")
async def check_certification_expirations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check certifications near expiry and create notifications for affected users
    and coordinators/admins in the same organization.
    """
    org_id = current_user.organization_id
    today = date.today()
    thresholds = {30, 15, 7}
    day_start = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)

    certs_query = db.query(UserCertification)
    if org_id is not None:
        certs_query = certs_query.filter(UserCertification.organization_id == org_id)
    certifications = certs_query.all()

    managers_query = db.query(User).filter(
        User.is_active.is_(True),
        User.role.in_([UserRole.COORDINATOR.value, UserRole.ADMIN.value]),
    )
    if org_id is not None:
        managers_query = managers_query.filter(User.organization_id == org_id)
    managers = managers_query.all()

    created = 0
    checked = 0

    for cert in certifications:
        if not cert.expiry_date:
            continue

        days_left = (cert.expiry_date - today).days
        if days_left not in thresholds and days_left >= 0:
            continue

        checked += 1
        priority = _priority_for_days(days_left)
        notification_type = _type_for_priority(priority)
        cert_name = cert.certification_type.name if cert.certification_type else "Certificacion"
        title = _build_title(days_left, cert_name)
        message = _build_message(days_left, cert_name, cert.expiry_date)
        link = f"/certifications?user_id={cert.user_id}"

        recipient_ids = {cert.user_id}
        recipient_ids.update(manager.id for manager in managers)

        for user_id in recipient_ids:
            existing = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.title == title,
                    Notification.link == link,
                    Notification.created_at >= day_start,
                )
                .first()
            )
            if existing:
                continue

            db.add(
                Notification(
                    user_id=user_id,
                    notification_type="certification_alert",
                    type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    link=link,
                    is_read=False,
                    organization_id=cert.organization_id,
                )
            )
            created += 1

    db.commit()
    return {"checked": checked, "created": created}


@router.get("/summary")
async def alerts_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get active certification alert summary by priority."""
    org_id = current_user.organization_id

    query = db.query(Notification).filter(
        Notification.notification_type == "certification_alert",
        Notification.is_read.is_(False),
    )
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        query = query.filter(Notification.user_id == current_user.id)
    elif org_id is not None:
        query = query.filter(Notification.organization_id == org_id)

    items = query.all()
    critical = sum(1 for item in items if item.priority == "critical")
    urgent = sum(1 for item in items if item.priority == "urgent")
    warning = sum(1 for item in items if item.priority == "warning")

    return {
        "total": len(items),
        "critical": critical,
        "urgent": urgent,
        "warning": warning,
    }
