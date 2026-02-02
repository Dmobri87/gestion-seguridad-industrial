from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.program import ProgramCreate, ProgramOut, ProgramUpdate
from app.models.program import Program
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/programs", tags=["Programas"])

@router.post("/", response_model=ProgramOut)
def create_program(
    program: ProgramCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crear un nuevo programa.
    
    Solo Administradores y Coordinadores pueden crear programas.
    """
    # Validar permisos
    if current_user["role"] not in ["Administrador", "Coordinador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear programas"
        )
    
    # Crear el programa
    new_program = Program(
        name=program.name,
        description=program.description,
        coordinator_id=program.coordinator_id
    )
    db.add(new_program)
    db.commit()
    db.refresh(new_program)
    return new_program


@router.get("/", response_model=list[ProgramOut])
def list_programs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todos los programas.
    
    Cualquier usuario autenticado puede ver los programas.
    """
    return db.query(Program).all()


@router.get("/{program_id}", response_model=ProgramOut)
def get_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtener un programa específico por ID.
    """
    program = db.query(Program).filter(Program.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programa con ID {program_id} no encontrado"
        )
    
    return program


@router.put("/{program_id}", response_model=ProgramOut)
def update_program(
    program_id: int,
    program_update: ProgramUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualizar un programa existente.
    
    Solo Administradores y Coordinadores pueden actualizar programas.
    Los campos no enviados en el JSON permanecen sin cambios.
    """
    # Validar permisos
    if current_user["role"] not in ["Administrador", "Coordinador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar programas"
        )
    
    # Buscar el programa en la base de datos
    program = db.query(Program).filter(Program.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programa con ID {program_id} no encontrado"
        )
    
    # Actualizar solo los campos que se enviaron (no son None)
    if program_update.name is not None:
        program.name = program_update.name
    if program_update.description is not None:
        program.description = program_update.description
    if program_update.coordinator_id is not None:
        program.coordinator_id = program_update.coordinator_id
    
    # Guardar los cambios en la base de datos
    db.commit()
    db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_200_OK)
def delete_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Eliminar un programa.
    
    Solo Administradores pueden eliminar programas.
    ADVERTENCIA: Esto también eliminará todas las actividades asociadas.
    """
    # Validar permisos - SOLO Administradores
    if current_user["role"] != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los Administradores pueden eliminar programas"
        )
    
    # Buscar el programa
    program = db.query(Program).filter(Program.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programa con ID {program_id} no encontrado"
        )
    
    # Guardar información antes de eliminar
    program_name = program.name
    
    # Eliminar el programa
    db.delete(program)
    db.commit()
    
    return {
        "message": "Programa eliminado exitosamente",
        "deleted_program": {
            "id": program_id,
            "name": program_name
        }
    }