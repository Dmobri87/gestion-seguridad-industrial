"""add_requires_evidence_to_planned_activities

Revision ID: b3f2e9a41c2d
Revises: a777130e9dfd
Create Date: 2026-02-21 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3f2e9a41c2d"
down_revision: Union[str, None] = "a777130e9dfd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Nuevo campo con default true para nuevas filas
    op.add_column(
        "planned_activities",
        sa.Column("requires_evidence", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # 2) Forzar true en todas las actividades ya creadas
    op.execute("UPDATE planned_activities SET requires_evidence = TRUE")


def downgrade() -> None:
    op.drop_column("planned_activities", "requires_evidence")

