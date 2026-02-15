"""add video status

Revision ID: 002_add_status
Revises: 001_initial
Create Date: MVP - Video status tracking

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_status"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE videostatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')")
    op.add_column(
        "videos",
        sa.Column("status", sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="videostatus"), nullable=False, server_default="PENDING"),
    )


def downgrade() -> None:
    op.drop_column("videos", "status")
    op.execute("DROP TYPE IF EXISTS videostatus")
