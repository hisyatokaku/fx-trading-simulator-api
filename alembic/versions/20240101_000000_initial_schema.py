"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scenarios table
    op.create_table(
        'scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime(), nullable=False),
        sa.Column('commission_rate', sa.Numeric(precision=10, scale=6), nullable=True, server_default='0'),
        sa.Column('time_interval_seconds', sa.Integer(), nullable=False, server_default='86400'),
        sa.Column('game_type', sa.String(length=20), nullable=True, server_default='ANY'),
        sa.Column('initial_balance', sa.Numeric(precision=20, scale=6), nullable=True, server_default='1000000'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_scenarios_id', 'scenarios', ['id'])
    op.create_index('ix_scenarios_name', 'scenarios', ['name'])

    # Create traders table
    op.create_table(
        'traders',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False, server_default='test'),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Create trading_sessions table
    op.create_table(
        'trading_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime(), nullable=False),
        sa.Column('current_datetime', sa.DateTime(), nullable=False),
        sa.Column('time_interval_seconds', sa.Integer(), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('jpy_balance', sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column('commission_rate', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['traders.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trading_sessions_id', 'trading_sessions', ['id'])

    # Create balances table
    op.create_table(
        'balances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=6), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['trading_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'timestamp', 'currency', name='uq_balance_session_time_currency')
    )
    op.create_index('ix_balances_id', 'balances', ['id'])

    # Create rates table
    op.create_table(
        'rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('rate_to_jpy', sa.Numeric(precision=20, scale=10), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('currency', 'timestamp', name='uq_rate_currency_timestamp')
    )
    op.create_index('ix_rates_id', 'rates', ['id'])
    op.create_index('ix_rates_currency', 'rates', ['currency'])
    op.create_index('ix_rates_timestamp', 'rates', ['timestamp'])
    op.create_index('ix_rate_currency_timestamp', 'rates', ['currency', 'timestamp'])


def downgrade() -> None:
    op.drop_table('balances')
    op.drop_table('trading_sessions')
    op.drop_table('traders')
    op.drop_table('rates')
    op.drop_table('scenarios')
