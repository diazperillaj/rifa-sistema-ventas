"""Extensión unaccent para buscar sin tildes

Revision ID: a3c1e2f4b5d6
Revises: fb8cf92ccd64
Create Date: 2026-09-16 18:00:00
"""
from collections.abc import Sequence

from alembic import op

revision: str = 'a3c1e2f4b5d6'
down_revision: str | None = 'fb8cf92ccd64'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
