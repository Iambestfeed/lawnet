"""Hoàn tất crawl manager

Revision ID: 3eee7adb95ca
Revises: e2306a4ba087
Create Date: 2025-01-24 14:46:30.934144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3eee7adb95ca'
down_revision: Union[str, None] = 'e2306a4ba087'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
