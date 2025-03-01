"""add_processing_models_and_relations

Revision ID: a1742e8d21a4
Revises: ced5e6e0d531
Create Date: 2025-02-01 14:50:45.573685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1742e8d21a4'
down_revision: Union[str, None] = 'ced5e6e0d531'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Tạo enum cho processing_status
    op.execute("""
        CREATE TYPE processing_status AS ENUM (
            'pending', 
            'processing', 
            'success', 
            'failed'
        )
    """)
    
    # Tạo bảng process_tracker
    op.create_table(
        'process_tracker',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('legal_documents.id')),
        sa.Column('article_id', sa.String(150)),
        sa.Column('status', sa.Enum('pending', 'processing', 'success', 'failed', name='processing_status')),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('finished_at', sa.DateTime()),
        sa.Column('error_log', sa.Text())
    )
    
    # Tạo bảng processed_articles
    op.create_table(
        'processed_articles',
        sa.Column('article_id', sa.String(150), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('legal_documents.id')),
        sa.Column('raw_content', sa.Text()),
        sa.Column('cleaned_content', sa.Text()),
        sa.Column('structural_metadata', sa.JSON()),
        sa.Column('process_tracker_id', sa.Integer(), sa.ForeignKey('process_tracker.id')),
        sa.Column('processed_at', sa.DateTime(), default=datetime.now)
    )
    
    # Thêm quan hệ cho legal_documents
    with op.batch_alter_table('legal_documents') as batch_op:
        batch_op.create_foreign_key(
            'fk_process_tracker_document',
            'process_tracker',
            ['id'], ['document_id']
        )
        batch_op.create_foreign_key(
            'fk_processed_articles_document',
            'processed_articles',
            ['id'], ['document_id']
        )

def downgrade():
    # Xóa bảng và enum
    op.drop_table('processed_articles')
    op.drop_table('process_tracker')
    op.execute("DROP TYPE processing_status")
    
    # Xóa foreign keys
    with op.batch_alter_table('legal_documents') as batch_op:
        batch_op.drop_constraint('fk_process_tracker_document')
        batch_op.drop_constraint('fk_processed_articles_document')
