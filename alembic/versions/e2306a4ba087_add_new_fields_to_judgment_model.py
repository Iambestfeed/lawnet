"""Add new fields to Judgment model

Revision ID: e2306a4ba087
Revises: 7e6b158c3bc4
Create Date: 2025-01-24 11:28:28.625360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2306a4ba087'
down_revision: Union[str, None] = '7e6b158c3bc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
