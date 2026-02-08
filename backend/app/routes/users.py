from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserOut
from app.models.user import User  # El molde que creamos antes
from app.core.database import get_db # El "enchufe" a la DB
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["Usuarios"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Buscar si el usuario ya existe en el archivo .db
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # 2. Encriptar la contraseña
    hashed_password = pwd_context.hash(user.password)
    
    # 3. Crear el nuevo registro usando el Modelo
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role
    )
    
    # 4. Guardar físicamente en el archivo
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user