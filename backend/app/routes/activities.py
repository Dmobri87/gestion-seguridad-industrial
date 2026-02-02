from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.activity import ActivityCreate, ActivityOut, ActivityUpdate
from app.models.activity import Activity
from app.models.program import Program
from app.core.dependencies import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/activities", tags=["Actividades"])

@router.post("/", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity: ActivityCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crear una nueva actividad (solo roles de mando).
    
    Roles permitidos: Administrador, Coordinador, Supervisor
    """
    # Validar permisos
    if current_user["role"] not in ["Administrador", "Coordinador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para crear actividades"
        )
    
    # Verificar que el programa existe
    program = db.query(Program).filter(Program.id == activity.program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programa con ID {activity.program_id} no existe"
        )
    
    # Crear la actividad en la base de datos
    new_activity = Activity(
        name=activity.name,
        description=activity.description,
        program_id=activity.program_id
    )
    
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity


@router.get("/", response_model=list[ActivityOut])
def list_activities(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todas las actividades.
    
    Cualquier usuario autenticado puede ver las actividades.
    """
    return db.query(Activity).all()


@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener una actividad específica por ID.
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {activity_id} no encontrada"
        )
    
    return activity


@router.get("/program/{program_id}", response_model=list[ActivityOut])
def list_activities_by_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todas las actividades de un programa específico.
    """
    # Verificar que el programa existe
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programa con ID {program_id} no existe"
        )
    
    return db.query(Activity).filter(Activity.program_id == program_id).all()


@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    activity_update: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualizar una actividad existente.
    
    Solo Administradores, Coordinadores y Supervisores pueden actualizar.
    Los campos no enviados en el JSON permanecen sin cambios.
    """
    # Validar permisos
    if current_user["role"] not in ["Administrador", "Coordinador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar actividades"
        )
    
    # Buscar la actividad
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {activity_id} no encontrada"
        )
    
    # Si se quiere cambiar el programa, verificar que existe
    if activity_update.program_id is not None:
        program = db.query(Program).filter(Program.id == activity_update.program_id).first()
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Programa con ID {activity_update.program_id} no existe"
            )
    
    # Actualizar solo los campos enviados
    if activity_update.name is not None:
        activity.name = activity_update.name
    if activity_update.description is not None:
        activity.description = activity_update.description
    if activity_update.program_id is not None:
        activity.program_id = activity_update.program_id
    
    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_200_OK)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar una actividad.
    
    Solo Administradores pueden eliminar actividades.
    ADVERTENCIA: Esto también eliminará todas las ejecuciones asociadas.
    """
    # Validar permisos - SOLO Administradores
    if current_user["role"] != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los Administradores pueden eliminar actividades"
        )
    
    # Buscar la actividad
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {activity_id} no encontrada"
        )
    
    # Guardar información antes de eliminar
    activity_name = activity.name
    
    # Eliminar la actividad
    db.delete(activity)
    db.commit()
    
    return {
        "message": "Actividad eliminada exitosamente",
        "deleted_activity": {
            "id": activity_id,
            "name": activity_name
        }
    }