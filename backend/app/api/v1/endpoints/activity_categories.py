from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

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


@router.get("/", response_model=List[ActivityCategoryWithCount])
async def get_activity_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar todas las categorías de actividades con conteo.
    """
    categories = db.query(ActivityCategory).filter(
        ActivityCategory.is_active == True
    ).order_by(ActivityCategory.display_order).all()

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

    return category


@router.post("/", response_model=ActivityCategoryResponse)
async def create_activity_category(
    category_data: ActivityCategoryCreate,
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

    category = ActivityCategory(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.put("/{category_id}", response_model=ActivityCategoryResponse)
async def update_activity_category(
    category_id: int,
    category_data: ActivityCategoryUpdate,
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
    return category


@router.delete("/{category_id}")
async def delete_activity_category(
    category_id: int,
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

    category.is_active = False
    db.commit()
    return {"message": "Categoría desactivada"}
