"""Scheduler: pages.last_polled_at + alerts.rule_id nullable (alertas de LiveDetector sin regla)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pages", sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("alerts", "rule_id", existing_type=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.alter_column("alerts", "rule_id", existing_type=sa.BigInteger(), nullable=False)
    op.drop_column("pages", "last_polled_at")
