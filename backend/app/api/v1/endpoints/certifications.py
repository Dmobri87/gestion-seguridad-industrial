from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.certification import CertificationType, UserCertification, CertificationStatus

router = APIRouter()


# Schemas
class CertificationTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    applies_to: str
    default_validity_days: int
    is_mandatory: bool
    model_config = ConfigDict(from_attributes=True)


class UserCertificationResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    certification_type_id: int
    certification_type_name: Optional[str] = None
    certificate_number: Optional[str] = None
    issuing_entity: Optional[str] = None
    issue_date: date
    expiry_date: date
    expiration_date: Optional[date] = None
    status: str
    days_to_expire: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class CertificationCreate(BaseModel):
    user_id: int
    certification_type_id: int
    certificate_number: Optional[str] = None
    issuing_entity: Optional[str] = None
    issue_date: date
    expiry_date: Optional[date] = None
    expiration_date: Optional[date] = None


def _enrich_certification(cert: UserCertification, db: Session) -> dict:
    """Enrich a UserCertification with joined data for the frontend."""
    today = date.today()
    days_to_expire = (cert.expiry_date - today).days

    user = db.query(User).filter(User.id == cert.user_id).first()
    user_name = user.full_name if user else ""

    cert_type = db.query(CertificationType).filter(CertificationType.id == cert.certification_type_id).first()
    cert_type_name = cert_type.name if cert_type else ""

    return {
        "id": cert.id,
        "user_id": cert.user_id,
        "user_name": user_name,
        "certification_type_id": cert.certification_type_id,
        "certification_type_name": cert_type_name,
        "certificate_number": cert.certificate_number,
        "issuing_entity": cert.issuing_entity,
        "issue_date": cert.issue_date,
        "expiry_date": cert.expiry_date,
        "expiration_date": cert.expiry_date,
        "status": cert.status,
        "days_to_expire": days_to_expire,
    }


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


@router.get("/user/{user_id}")
async def get_user_certifications(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Listar certificaciones de un usuario (enriquecidas para el frontend)."""
    # Fix H-1: Authorization check — TAE/PSE can only view their own certifications
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        if user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No autorizado para ver estas certificaciones"
            )
    else:
        # Admin, Coordinator, Supervisor: enforce organization scoping
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if (
            current_user.organization_id
            and target_user.organization_id
            and target_user.organization_id != current_user.organization_id
        ):
            raise HTTPException(
                status_code=403,
                detail="No autorizado para ver estas certificaciones"
            )

    certifications = db.query(UserCertification).filter(
        UserCertification.user_id == user_id
    ).all()

    today = date.today()
    result = []
    for cert in certifications:
        days_until_expiry = (cert.expiry_date - today).days
        if days_until_expiry < 0:
            cert.status = CertificationStatus.EXPIRED.value
        elif days_until_expiry <= 30:
            cert.status = CertificationStatus.EXPIRING_SOON.value
        else:
            cert.status = CertificationStatus.ACTIVE.value
        result.append(_enrich_certification(cert, db))

    db.commit()
    return result


@router.post("/")
async def create_certification(
    data: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar nueva certificación."""
    resolved_expiry = data.expiry_date or data.expiration_date
    if not resolved_expiry:
        raise HTTPException(status_code=422, detail="Se requiere expiry_date o expiration_date")

    # Fix H-1: TAE/PSE can only create certifications attributed to themselves
    if current_user.role in (UserRole.TAE.value, UserRole.PSE.value):
        data.user_id = current_user.id

    certification = UserCertification(
        user_id=data.user_id,
        certification_type_id=data.certification_type_id,
        certificate_number=data.certificate_number,
        issuing_entity=data.issuing_entity,
        issue_date=data.issue_date,
        expiry_date=resolved_expiry,
        status=CertificationStatus.ACTIVE.value,
        organization_id=current_user.organization_id
    )
    db.add(certification)
    db.commit()
    db.refresh(certification)
    return _enrich_certification(certification, db)


@router.get("/expiring")
async def get_expiring_certifications(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener certificaciones próximas a vencer (formato compatible con frontend)."""
    today = date.today()
    expiry_limit = today + timedelta(days=days)

    query = db.query(UserCertification).join(User)

    if current_user.organization_id:
        query = query.filter(User.organization_id == current_user.organization_id)

    certifications = query.filter(
        UserCertification.expiry_date <= expiry_limit,
        UserCertification.expiry_date >= today
    ).all()

    result = [_enrich_certification(cert, db) for cert in certifications]
    return sorted(result, key=lambda x: x["days_to_expire"])


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

    expired = expiring_7 = expiring_15 = expiring_30 = active = 0

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
