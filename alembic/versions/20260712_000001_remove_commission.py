"""Remove commission columns

Revision ID: 002
Revises: 001
Create Date: 2026-07-12

"""
from typing import Sequence, Union
from alembic import op

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('scenarios', 'commission_rate')
    op.drop_column('trading_sessions', 'commission_rate')


def downgrade() -> None:
    import sqlalchemy as sa
    op.add_column('trading_sessions', sa.Column('commission_rate', sa.Numeric(precision=10, scale=6), nullable=True))
    op.add_column('scenarios', sa.Column('commission_rate', sa.Numeric(precision=10, scale=6), nullable=True, server_default='0'))
