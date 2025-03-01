"""Add judgment metadata fields

Revision ID: 7e6b158c3bc4
Revises: 1759c69cabc8
Create Date: 2025-01-24 11:09:35.934708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e6b158c3bc4'
down_revision: Union[str, None] = '1759c69cabc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
