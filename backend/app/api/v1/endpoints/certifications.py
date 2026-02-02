from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.certification import CertificationType, UserCertification, CertificationStatus

router = APIRouter()


# Schemas
class CertificationTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    applies_to: str
    default_validity_days: int
    is_mandatory: bool
    model_config = ConfigDict(from_attributes=True)


class UserCertificationResponse(BaseModel):
    id: int
    user_id: int
    certification_type_id: int
    certificate_number: Optional[str] = None
    issue_date: date
    expiry_date: date
    status: str
    model_config = ConfigDict(from_attributes=True)


class CertificationCreate(BaseModel):
    user_id: int
    certification_type_id: int
    certificate_number: Optional[str] = None
    issuing_entity: Optional[str] = None
    issue_date: date
    expiry_date: date


@router.get("/types", response_model=List[CertificationTypeResponse])
async def get_certification_types(
    applies_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar tipos de certificaciones."""
    query = db.query(CertificationType).filter(CertificationType.is_active == True)
    if applies_to:
        query = query.filter(CertificationType.applies_to == applies_to)
    return query.all()


@router.get("/user/{user_id}", response_model=List[UserCertificationResponse])
async def get_user_certifications(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar certificaciones de un usuario."""
    certifications = db.query(UserCertification).filter(
        UserCertification.user_id == user_id
    ).all()

    # Actualizar estados basados en fecha de vencimiento
    today = date.today()
    for cert in certifications:
        days_until_expiry = (cert.expiry_date - today).days
        if days_until_expiry < 0:
            cert.status = CertificationStatus.EXPIRED.value
        elif days_until_expiry <= 30:
            cert.status = CertificationStatus.EXPIRING_SOON.value
        else:
            cert.status = CertificationStatus.ACTIVE.value

    db.commit()
    return certifications


@router.post("/", response_model=UserCertificationResponse)
async def create_certification(
    data: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar nueva certificación."""
    certification = UserCertification(
        **data.model_dump(),
        status=CertificationStatus.ACTIVE.value,
        organization_id=current_user.organization_id
    )
    db.add(certification)
    db.commit()
    db.refresh(certification)
    return certification


@router.get("/expiring")
async def get_expiring_certifications(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener certificaciones próximas a vencer."""
    today = date.today()
    expiry_limit = today + timedelta(days=days)

    query = db.query(UserCertification).join(User)

    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    certifications = query.filter(
        UserCertification.expiry_date <= expiry_limit,
        UserCertification.expiry_date >= today
    ).all()

    result = []
    for cert in certifications:
        user = db.query(User).filter(User.id == cert.user_id).first()
        cert_type = db.query(CertificationType).filter(CertificationType.id == cert.certification_type_id).first()
        days_until = (cert.expiry_date - today).days

        result.append({
            "certification_id": cert.id,
            "user_id": cert.user_id,
            "user_name": user.full_name if user else "",
            "certification_type": cert_type.name if cert_type else "",
            "expiry_date": cert.expiry_date.isoformat(),
            "days_until_expiry": days_until,
            "priority": "critical" if days_until <= 7 else ("urgent" if days_until <= 15 else "warning")
        })

    return sorted(result, key=lambda x: x["days_until_expiry"])


@router.get("/summary")
async def get_certifications_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resumen de certificaciones."""
    query = db.query(UserCertification).join(User)

    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    certifications = query.all()
    today = date.today()

    expired = 0
    expiring_7 = 0
    expiring_15 = 0
    expiring_30 = 0
    active = 0

    for cert in certifications:
        days = (cert.expiry_date - today).days
        if days < 0:
            expired += 1
        elif days <= 7:
            expiring_7 += 1
        elif days <= 15:
            expiring_15 += 1
        elif days <= 30:
            expiring_30 += 1
        else:
            active += 1

    return {
        "total": len(certifications),
        "active": active,
        "expiring_7_days": expiring_7,
        "expiring_15_days": expiring_15,
        "expiring_30_days": expiring_30,
        "expired": expired
    }
