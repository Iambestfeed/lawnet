"""add_process_tracker_table

Revision ID: ced5e6e0d531
Revises: 3eee7adb95ca
Create Date: 2025-01-27 16:50:00.199803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ced5e6e0d531'
down_revision: Union[str, None] = '3eee7adb95ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'process_tracker',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.String(length=255), nullable=False),
        sa.Column('document_type', sa.Enum('law', 'judgment', 'qa', name='doc_type'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'success', 'failed', name='process_status'), server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('finished_at', sa.DateTime()),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('error_log', sa.Text()),
        sa.Column('crawl_tracker_id', sa.Integer(), sa.ForeignKey('crawl_tracker.id')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Tạo indexes
    op.create_index('ix_proc_tracker_doc_id', 'process_tracker', ['document_id'])
    op.create_index('ix_proc_tracker_status', 'process_tracker', ['status'])
    op.create_index('ix_proc_tracker_type', 'process_tracker', ['document_type'])

def downgrade():
    op.drop_table('process_tracker')
    op.drop_index('ix_proc_tracker_doc_id')
    op.drop_index('ix_proc_tracker_status')
    op.drop_index('ix_proc_tracker_type')
