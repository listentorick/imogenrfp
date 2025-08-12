"""Add Excel support to questions

Revision ID: e4f8c9d12345
Revises: d8d202e743c0
Create Date: 2025-08-02 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f8c9d12345'
down_revision: Union[str, None] = 'd8d202e743c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Excel-specific fields to questions table
    op.add_column('questions', sa.Column('answer_cell_reference', sa.String(10), nullable=True))
    op.add_column('questions', sa.Column('cell_confidence', sa.Numeric(precision=3, scale=2), nullable=True))
    op.add_column('questions', sa.Column('sheet_name', sa.String(255), nullable=True))
    op.add_column('questions', sa.Column('document_type', sa.String(50), nullable=True))
    
    # Create indexes for performance
    op.create_index('idx_questions_document_type', 'questions', ['document_type'])
    op.create_index('idx_questions_answer_cell', 'questions', ['answer_cell_reference'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_questions_answer_cell', table_name='questions')
    op.drop_index('idx_questions_document_type', table_name='questions')
    
    # Remove columns
    op.drop_column('questions', 'document_type')
    op.drop_column('questions', 'sheet_name')
    op.drop_column('questions', 'cell_confidence')
    op.drop_column('questions', 'answer_cell_reference')