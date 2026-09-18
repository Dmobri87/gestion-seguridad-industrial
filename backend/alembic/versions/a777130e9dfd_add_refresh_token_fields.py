"""add_refresh_token_fields

Revision ID: a777130e9dfd
Revises: 
Create Date: 2026-02-14 21:37:20.528225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a777130e9dfd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('refresh_token_hash', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('refresh_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_users_refresh_token_hash'), 'users', ['refresh_token_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_refresh_token_hash'), table_name='users')
    op.drop_column('users', 'refresh_token_expires_at')
    op.drop_column('users', 'refresh_token_hash')
