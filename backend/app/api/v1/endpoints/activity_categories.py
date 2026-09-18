from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, ensure_org_access
from app.core.audit import log_audit
from app.models.user import User, UserRole
from app.models.activity_category import ActivityCategory
from sqlalchemy import or_
from app.schemas.planning import (
    ActivityCategoryResponse,
    ActivityCategoryCreate,
    ActivityCategoryUpdate,
    ActivityCategoryWithCount
)

router = APIRouter()


@router.get("/", response_model=List[ActivityCategoryWithCount])
async def get_activity_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar todas las categorías de actividades con conteo.
    """
    query = db.query(ActivityCategory).filter(ActivityCategory.is_active == True)
    if current_user.organization_id:
        query = query.filter(
            or_(
                ActivityCategory.organization_id == None,
                ActivityCategory.organization_id == current_user.organization_id
            )
        )
    categories = query.order_by(ActivityCategory.display_order).offset(skip).limit(limit).all()

    result = []
    for cat in categories:
        cat_dict = ActivityCategoryWithCount.model_validate(cat)
        cat_dict.activities_count = len(cat.activity_templates) if cat.activity_templates else 0
        result.append(cat_dict)

    return result


@router.get("/{category_id}", response_model=ActivityCategoryResponse)
async def get_activity_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener categoría por ID.
    """
    category = db.query(ActivityCategory).filter(
        ActivityCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    ensure_org_access(current_user, category, "categoría", allow_global=True)

    return category


@router.post("/", response_model=ActivityCategoryResponse)
async def create_activity_category(
    category_data: ActivityCategoryCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear nueva categoría de actividades.
    """
    # Verificar código único
    existing = db.query(ActivityCategory).filter(
        ActivityCategory.code == category_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de categoría ya existe"
        )

    organization_id = category_data.organization_id
    if current_user.organization_id:
        organization_id = current_user.organization_id

    category = ActivityCategory(**category_data.model_dump(), organization_id=organization_id)
    db.add(category)
    db.commit()
    db.refresh(category)

    log_audit(
        db=None,
        action="ACTIVITY_CATEGORY_CREATED",
        resource_type="activity_categories",
        resource_id=category.id,
        current_user=current_user,
        request=request,
        description="Categoría creada",
    )

    return category


@router.put("/{category_id}", response_model=ActivityCategoryResponse)
async def update_activity_category(
    category_id: int,
    category_data: ActivityCategoryUpdate,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """
    Actualizar categoría de actividades.
    """
    category = db.query(ActivityCategory).filter(
        ActivityCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    ensure_org_access(current_user, category, "categoría")

    # Verificar código único si se cambia
    update_data = category_data.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"] != category.code:
        existing = db.query(ActivityCategory).filter(
            ActivityCategory.code == update_data["code"],
            ActivityCategory.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código de categoría ya existe"
            )

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    log_audit(
        db=None,
        action="ACTIVITY_CATEGORY_UPDATED",
        resource_type="activity_categories",
        resource_id=category.id,
        current_user=current_user,
        request=request,
        description="Categoría actualizada",
    )
    return category


@router.delete("/{category_id}")
async def delete_activity_category(
    category_id: int,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Desactivar categoría de actividades (soft delete).
    """
    category = db.query(ActivityCategory).filter(
        ActivityCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    ensure_org_access(current_user, category, "categoría")

    category.is_active = False
    db.commit()
    log_audit(
        db=None,
        action="ACTIVITY_CATEGORY_DELETED",
        resource_type="activity_categories",
        resource_id=category.id,
        current_user=current_user,
        request=request,
        description="Categoría desactivada",
    )
    return {"message": "Categoría desactivada"}
