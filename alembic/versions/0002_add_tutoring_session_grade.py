"""Add grade column to tutoring_sessions

Revision ID: 0002_add_tutoring_session_grade
Revises: 0001_add_ai_feedback
Create Date: 2025-12-05
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_tutoring_session_grade'
down_revision = '0001_add_ai_feedback'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('tutoring_sessions')] if inspector.has_table('tutoring_sessions') else []
    if 'grade' not in existing_columns:
        op.add_column('tutoring_sessions', sa.Column('grade', sa.String(), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('tutoring_sessions')] if inspector.has_table('tutoring_sessions') else []
    if 'grade' in existing_columns:
        op.drop_column('tutoring_sessions', 'grade')
