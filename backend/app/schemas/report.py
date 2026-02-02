from pydantic import BaseModel

class ProgramReport(BaseModel):
    program_id: int
    program_name: str
    total_executions: int
    status_summary: dict # Ejemplo: {"Completado": 10, "Pendiente": 2}

    class Config:
        from_attributes = True