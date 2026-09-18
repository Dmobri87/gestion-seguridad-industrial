from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.activity_category import ActivityCategory
from app.schemas.planning import (
    ActivityCategoryResponse,
    ActivityCategoryCreate,
    ActivityCategoryUpdate,
    ActivityCategoryWithCount
)

router = APIRouter()

COORDINATOR_ROLES = {UserRole.ADMIN.value, UserRole.COORDINATOR.value, UserRole.SUPERVISOR.value}


@router.get("/", response_model=List[ActivityCategoryWithCount])
async def get_activity_categories(
    coordinator_only: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar categorías de actividades con conteo.
    - TAEs/PSEs: solo ven categorías normales (coordinator_only=False)
    - Coordinadores/Admin: pueden ver todas o filtrar por coordinator_only
    """
    query = db.query(ActivityCategory).filter(ActivityCategory.is_active == True)

    is_coordinator = current_user.role in COORDINATOR_ROLES

    if coordinator_only is not None:
        # Filtro explícito — solo coordinadores pueden ver las de coordinador
        if coordinator_only and not is_coordinator:
            return []
        query = query.filter(ActivityCategory.coordinator_only == coordinator_only)
    elif not is_coordinator:
        # TAEs/PSEs: nunca ven las de coordinador
        query = query.filter(ActivityCategory.coordinator_only == False)

    categories = query.order_by(ActivityCategory.display_order).all()

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
    """Obtener categoría por ID."""
    category = db.query(ActivityCategory).filter(
        ActivityCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )

    # TAEs no pueden ver categorías de coordinador
    if category.coordinator_only and current_user.role not in COORDINATOR_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta categoría"
        )

    return category


@router.post("/", response_model=ActivityCategoryResponse)
async def create_activity_category(
    category_data: ActivityCategoryCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Crear nueva categoría de actividades."""
    existing = db.query(ActivityCategory).filter(
        ActivityCategory.code == category_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de categoría ya existe"
        )

    category = ActivityCategory(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.put("/{category_id}", response_model=ActivityCategoryResponse)
async def update_activity_category(
    category_id: int,
    category_data: ActivityCategoryUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Actualizar categoría de actividades."""
    category = db.query(ActivityCategory).filter(
        ActivityCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )

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
    return category


@router.delete("/{category_id}")
async def delete_activity_category(
    category_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Desactivar categoría de actividades (soft delete)."""
    category = db.query(ActivityCategory).filter(
        ActivityCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )

    category.is_active = False
    db.commit()
    return {"message": "Categoría desactivada"}
