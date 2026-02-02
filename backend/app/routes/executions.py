from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.execution import ExecutionCreate, ExecutionOut, ExecutionUpdate
from app.models.execution import Execution
from app.models.activity import Activity
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/executions", tags=["Ejecuciones Diarias"])

@router.post("/", response_model=ExecutionOut, status_code=status.HTTP_201_CREATED)
def register_execution(
    execution: ExecutionCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Registrar una nueva ejecución de actividad.
    
    El usuario solo puede ejecutar actividades que tenga asignadas.
    """
    from app.models.activity_assignment import ActivityAssignment  # Importar aquí
    
    # Verificar que la actividad existe
    activity = db.query(Activity).filter(Activity.id == execution.activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {execution.activity_id} no existe"
        )
    
    # Obtener el ID real del usuario
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # 🆕 VALIDAR QUE EL USUARIO TENGA LA ACTIVIDAD ASIGNADA
    assignment = db.query(ActivityAssignment).filter(
        ActivityAssignment.activity_id == execution.activity_id,
        ActivityAssignment.user_id == user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes asignada esta actividad. Contacta a tu supervisor."
        )
    
    # Crear la ejecución
    new_execution = Execution(
        activity_id=execution.activity_id,
        user_id=user.id,
        observation=execution.observation,
        status=execution.status
    )
    
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)
    return new_execution

@router.get("/", response_model=list[ExecutionOut])
def list_executions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todas las ejecuciones.
    
    Los administradores y supervisores ven todas las ejecuciones.
    Los demás usuarios solo ven sus propias ejecuciones.
    """
    if current_user["role"] in ["Administrador", "Supervisor"]:
        # Ver todas las ejecuciones
        return db.query(Execution).all()
    else:
        # Solo ver las propias
        user = db.query(User).filter(User.email == current_user["email"]).first()
        return db.query(Execution).filter(Execution.user_id == user.id).all()


@router.get("/my-executions", response_model=list[ExecutionOut])
def list_my_executions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar solo las ejecuciones del usuario actual.
    """
    user = db.query(User).filter(User.email == current_user["email"]).first()
    return db.query(Execution).filter(Execution.user_id == user.id).all()


@router.get("/activity/{activity_id}", response_model=list[ExecutionOut])
def list_executions_by_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todas las ejecuciones de una actividad específica.
    """
    # Verificar que la actividad existe
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad con ID {activity_id} no existe"
        )
    
    return db.query(Execution).filter(Execution.activity_id == activity_id).all()


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener una ejecución específica por ID.
    """
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejecución con ID {execution_id} no encontrada"
        )
    
    # Verificar permisos: solo el dueño o roles de mando pueden ver
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if execution.user_id != user.id and current_user["role"] not in ["Administrador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta ejecución"
        )
    
    return execution


@router.put("/{execution_id}", response_model=ExecutionOut)
def update_execution(
    execution_id: int,
    execution_update: ExecutionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualizar una ejecución existente.
    
    Los usuarios solo pueden actualizar sus propias ejecuciones.
    Administradores y Supervisores pueden actualizar cualquier ejecución.
    """
    # Buscar la ejecución
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejecución con ID {execution_id} no encontrada"
        )
    
    # Verificar permisos
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if execution.user_id != user.id and current_user["role"] not in ["Administrador", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar esta ejecución"
        )
    
    # Actualizar solo los campos enviados
    if execution_update.observation is not None:
        execution.observation = execution_update.observation
    if execution_update.status is not None:
        execution.status = execution_update.status
    
    db.commit()
    db.refresh(execution)
    return execution


@router.delete("/{execution_id}", status_code=status.HTTP_200_OK)
def delete_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar una ejecución.
    
    Solo Administradores pueden eliminar ejecuciones.
    """
    # Validar permisos - SOLO Administradores
    if current_user["role"] != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los Administradores pueden eliminar ejecuciones"
        )
    
    # Buscar la ejecución
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejecución con ID {execution_id} no encontrada"
        )
    
    # Guardar información antes de eliminar
    activity_id = execution.activity_id
    execution_date = execution.execution_date
    
    # Eliminar la ejecución
    db.delete(execution)
    db.commit()
    
    return {
        "message": "Ejecución eliminada exitosamente",
        "deleted_execution": {
            "id": execution_id,
            "activity_id": activity_id,
            "execution_date": str(execution_date)
        }
    }