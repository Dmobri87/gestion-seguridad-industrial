"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-12
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Crear el esquema completo usando los modelos actuales
    from app.core.database import Base
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    # Downgrade no destructivo por seguridad en producción
    pass
