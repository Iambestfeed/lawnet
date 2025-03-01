"""empty message

Revision ID: 1759c69cabc8
Revises: 66c670e95906
Create Date: 2025-01-24 10:55:35.692085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1759c69cabc8'
down_revision: Union[str, None] = '66c670e95906'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
