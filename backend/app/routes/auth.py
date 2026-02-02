from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token

router = APIRouter(tags=["Autenticación"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint para autenticar usuarios y generar tokens JWT.
    
    - **username**: Email del usuario (OAuth2 lo llama username)
    - **password**: Contraseña sin encriptar
    
    Returns: Token JWT válido por 30 minutos
    """
    # 1. Buscar usuario por email (OAuth2 usa 'username' pero nosotros usamos email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Verificar la contraseña usando la función de security.py
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Crear el token JWT con los datos del usuario
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }