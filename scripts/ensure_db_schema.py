"""Ensure DB schema has required columns for runtime.

This helper detects missing columns on key tables (currently `users`) and
adds them using ALTER TABLE. Run once after pulling model changes.

Usage:
    python scripts/ensure_db_schema.py

Note: This is a small convenience tool. For production use, use Alembic migrations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.db.session import engine

REQUIRED_USER_COLUMNS = {
    'hashed_password': 'VARCHAR',
    'updated_at': 'TIMESTAMP'
}


def ensure_users_table_columns():
    inspector = inspect(engine)
    if 'users' not in inspector.get_table_names():
        print('Users table not found. Create tables first:')
        print('  python -c "from app.db.models import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"')
        return

    columns = [col['name'] for col in inspector.get_columns('users')]
    with engine.connect() as conn:
        for col_name, col_type in REQUIRED_USER_COLUMNS.items():
            if col_name not in columns:
                print(f"Adding missing column '{col_name}' to 'users' table")
                if col_type.upper() == 'VARCHAR':
                    sql = text(f"ALTER TABLE users ADD COLUMN {col_name} VARCHAR;")
                elif col_type.upper() == 'TIMESTAMP':
                    sql = text(f"ALTER TABLE users ADD COLUMN {col_name} TIMESTAMP;")
                else:
                    sql = text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
                try:
                    conn.execute(sql)
                    print(f"Column '{col_name}' added successfully.")
                except Exception as e:
                    print(f"Failed to add column '{col_name}': {e}")
            else:
                print(f"Column '{col_name}' already exists.")


if __name__ == '__main__':
    ensure_users_table_columns()
    print('Schema check complete.')
