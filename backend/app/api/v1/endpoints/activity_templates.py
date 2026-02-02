from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.activity_category import ActivityCategory, ActivityTemplate
from app.schemas.planning import (
    ActivityTemplateResponse,
    ActivityTemplateCreate,
    ActivityTemplateUpdate,
    ActivityTemplateWithCategory
)

router = APIRouter()


@router.get("/", response_model=List[ActivityTemplateWithCategory])
async def get_activity_templates(
    category_id: Optional[int] = None,
    is_critical: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar todas las plantillas de actividades.
    """
    query = db.query(ActivityTemplate).options(
        joinedload(ActivityTemplate.category)
    ).filter(ActivityTemplate.is_active == True)

    if category_id:
        query = query.filter(ActivityTemplate.category_id == category_id)

    if is_critical is not None:
        query = query.filter(ActivityTemplate.is_critical == is_critical)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ActivityTemplate.name.ilike(search_term)) |
            (ActivityTemplate.code.ilike(search_term))
        )

    templates = query.order_by(
        ActivityTemplate.category_id,
        ActivityTemplate.display_order
    ).all()

    result = []
    for tmpl in templates:
        tmpl_dict = {
            **ActivityTemplateResponse.model_validate(tmpl).model_dump(),
            "category_name": tmpl.category.name if tmpl.category else "",
            "category_code": tmpl.category.code if tmpl.category else "",
            "category_color": tmpl.category.color if tmpl.category else "#1890ff"
        }
        result.append(ActivityTemplateWithCategory(**tmpl_dict))

    return result


@router.get("/by-category", response_model=dict)
async def get_templates_grouped_by_category(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener plantillas agrupadas por categoría.
    Útil para la pantalla de planificación.
    """
    categories = db.query(ActivityCategory).options(
        joinedload(ActivityCategory.activity_templates)
    ).filter(
        ActivityCategory.is_active == True
    ).order_by(ActivityCategory.display_order).all()

    result = {}
    for cat in categories:
        templates = [
            ActivityTemplateResponse.model_validate(tmpl).model_dump()
            for tmpl in cat.activity_templates
            if tmpl.is_active
        ]
        result[cat.code] = {
            "id": cat.id,
            "name": cat.name,
            "code": cat.code,
            "color": cat.color,
            "icon": cat.icon,
            "templates": sorted(templates, key=lambda x: x["display_order"])
        }

    return result


@router.get("/{template_id}", response_model=ActivityTemplateWithCategory)
async def get_activity_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener plantilla por ID.
    """
    template = db.query(ActivityTemplate).options(
        joinedload(ActivityTemplate.category)
    ).filter(ActivityTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla no encontrada"
        )

    return {
        **ActivityTemplateResponse.model_validate(template).model_dump(),
        "category_name": template.category.name if template.category else "",
        "category_code": template.category.code if template.category else "",
        "category_color": template.category.color if template.category else "#1890ff"
    }


@router.post("/", response_model=ActivityTemplateResponse)
async def create_activity_template(
    template_data: ActivityTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear nueva plantilla de actividad.
    """
    # Verificar que la categoría existe
    category = db.query(ActivityCategory).filter(
        ActivityCategory.id == template_data.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )

    # Verificar código único si se proporciona
    if template_data.code:
        existing = db.query(ActivityTemplate).filter(
            ActivityTemplate.code == template_data.code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código de actividad ya existe"
            )

    template = ActivityTemplate(**template_data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.put("/{template_id}", response_model=ActivityTemplateResponse)
async def update_activity_template(
    template_id: int,
    template_data: ActivityTemplateUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.COORDINATOR.value])),
    db: Session = Depends(get_db)
):
    """
    Actualizar plantilla de actividad.
    """
    template = db.query(ActivityTemplate).filter(
        ActivityTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla no encontrada"
        )

    update_data = template_data.model_dump(exclude_unset=True)

    # Verificar categoría si se cambia
    if "category_id" in update_data:
        category = db.query(ActivityCategory).filter(
            ActivityCategory.id == update_data["category_id"]
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )

    # Verificar código único si se cambia
    if "code" in update_data and update_data["code"] != template.code:
        existing = db.query(ActivityTemplate).filter(
            ActivityTemplate.code == update_data["code"],
            ActivityTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código de actividad ya existe"
            )

    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_activity_template(
    template_id: int,
    current_user: User = Depends(require_roles([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Desactivar plantilla de actividad (soft delete).
    """
    template = db.query(ActivityTemplate).filter(
        ActivityTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla no encontrada"
        )

    template.is_active = False
    db.commit()
    return {"message": "Plantilla desactivada"}
