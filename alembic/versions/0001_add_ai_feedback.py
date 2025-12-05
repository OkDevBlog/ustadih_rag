"""Add ai_feedback JSON column to ministry_exam_attempts

Revision ID: 0001_add_ai_feedback
Revises: None
Create Date: 2025-12-05
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_ai_feedback'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable JSON column `ai_feedback` to ministry_exam_attempts if it doesn't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('ministry_exam_attempts')] if inspector.has_table('ministry_exam_attempts') else []
    if 'ai_feedback' not in existing_columns:
        op.add_column(
            'ministry_exam_attempts',
            sa.Column('ai_feedback', sa.JSON(), nullable=True)
        )


def downgrade():
    # Drop column only if it exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('ministry_exam_attempts')] if inspector.has_table('ministry_exam_attempts') else []
    if 'ai_feedback' in existing_columns:
        op.drop_column('ministry_exam_attempts', 'ai_feedback')
