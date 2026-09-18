# Ejecucion Local Sin Docker (Windows)

## 1) Backend

```powershell
Set-Location "C:\Users\deivi\OneDrive\Escritorio\Cerrejon - Emergencias\gestion_proyectos - copia\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Notas:
- Para desarrollo local usa SQLite (`DATABASE_URL=sqlite:///./seguridad_industrial.db` en `.env`).
- API y docs: `http://127.0.0.1:8000` y `http://127.0.0.1:8000/docs`.

## 2) Frontend

En otra terminal:

```powershell
Set-Location "C:\Users\deivi\OneDrive\Escritorio\Cerrejon - Emergencias\gestion_proyectos - copia\frontend"
npm install
npm run dev
```

Notas:
- Frontend: `http://localhost:3000`
- Vite proxy ya apunta a backend local (`/api` -> `http://localhost:8000`).

## 3) Verificaciones rapidas

```powershell
# Backend tests
Set-Location "C:\Users\deivi\OneDrive\Escritorio\Cerrejon - Emergencias\gestion_proyectos - copia\backend"
python -m pytest -q

# Frontend build
Set-Location "C:\Users\deivi\OneDrive\Escritorio\Cerrejon - Emergencias\gestion_proyectos - copia\frontend"
npm run build
```

