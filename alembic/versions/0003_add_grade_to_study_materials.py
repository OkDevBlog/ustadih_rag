"""Add grade column to study_materials

Revision ID: 0003_add_grade_to_study_materials
Revises: 0002_add_tutoring_session_grade
Create Date: 2025-12-05
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_grade_to_study_materials'
down_revision = '0002_add_tutoring_session_grade'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('study_materials')] if inspector.has_table('study_materials') else []
    if 'grade' not in existing_columns:
        op.add_column('study_materials', sa.Column('grade', sa.String(), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('study_materials')] if inspector.has_table('study_materials') else []
    if 'grade' in existing_columns:
        op.drop_column('study_materials', 'grade')
