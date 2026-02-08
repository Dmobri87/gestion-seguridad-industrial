from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.assignment import AssignmentCreate, AssignmentOut
from app.models.activity_assignment import ActivityAssignment
from app.models.activity import Activity
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/assignments", tags=["Asignaciones"])

@router.post("/", response_model=list[AssignmentOut], status_code=status.HTTP_201_CREATED)
def assign_activity_to_users(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Asignar una actividad a uno o más usuarios.
    
    Solo Administradores y Supervisores pueden asignar.
    """
    # Validar permisos
    if current_user["role"] not in ["Administrador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Administradores y Supervisores pueden asignar actividades"
        )
    
    # Verificar que la actividad existe
    activity = db.query(Activity).filter(Activity.id == assignment.activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {assignment.activity_id} no existe"
        )
    
    # Obtener el ID del usuario que está asignando
    assigner = db.query(User).filter(User.email == current_user["email"]).first()
    
    # Verificar que todos los usuarios existen
    users = db.query(User).filter(User.id.in_(assignment.user_ids)).all()
    if len(users) != len(assignment.user_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más usuarios no existen"
        )
    
    # Crear asignaciones
    new_assignments = []
    for user_id in assignment.user_ids:
        # Verificar si ya existe la asignación
        existing = db.query(ActivityAssignment).filter(
            ActivityAssignment.activity_id == assignment.activity_id,
            ActivityAssignment.user_id == user_id
        ).first()
        
        if not existing:
            new_assignment = ActivityAssignment(
                activity_id=assignment.activity_id,
                user_id=user_id,
                assigned_by=assigner.id
            )
            db.add(new_assignment)
            new_assignments.append(new_assignment)
    
    db.commit()
    
    # Refrescar todas las asignaciones
    for assignment in new_assignments:
        db.refresh(assignment)
    
    return new_assignments


@router.get("/activity/{activity_id}", response_model=list[AssignmentOut])
def get_assignments_by_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener todos los usuarios asignados a una actividad específica.
    """
    # Verificar que la actividad existe
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {activity_id} no existe"
        )
    
    assignments = db.query(ActivityAssignment).filter(
        ActivityAssignment.activity_id == activity_id
    ).all()
    
    return assignments


@router.get("/user/{user_id}", response_model=list[AssignmentOut])
def get_assignments_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener todas las actividades asignadas a un usuario específico.
    
    Los usuarios solo pueden ver sus propias asignaciones.
    Administradores y Supervisores pueden ver las de cualquiera.
    """
    # Obtener usuario actual
    current_user_obj = db.query(User).filter(User.email == current_user["email"]).first()
    
    # Validar permisos
    if current_user_obj.id != user_id and current_user["role"] not in ["Administrador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estas asignaciones"
        )
    
    assignments = db.query(ActivityAssignment).filter(
        ActivityAssignment.user_id == user_id
    ).all()
    
    return assignments


@router.get("/my-assignments", response_model=list[AssignmentOut])
def get_my_assignments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener las actividades asignadas al usuario actual.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    
    assignments = db.query(ActivityAssignment).filter(
        ActivityAssignment.user_id == user.id
    ).all()
    
    return assignments


@router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
def remove_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar una asignación.
    
    Solo Administradores y Supervisores pueden eliminar asignaciones.
    """
    # Validar permisos
    if current_user["role"] not in ["Administrador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo Administradores y Supervisores pueden eliminar asignaciones"
        )
    
    # Buscar la asignación
    assignment = db.query(ActivityAssignment).filter(
        ActivityAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asignación con ID {assignment_id} no encontrada"
        )
    
    # Guardar información antes de eliminar
    activity_id = assignment.activity_id
    user_id = assignment.user_id
    
    # Eliminar
    db.delete(assignment)
    db.commit()
    
    return {
        "message": "Asignación eliminada exitosamente",
        "deleted_assignment": {
            "id": assignment_id,
            "activity_id": activity_id,
            "user_id": user_id
        }
    }