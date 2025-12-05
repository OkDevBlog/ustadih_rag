from sqlalchemy import text, inspect
from app.db.session import engine
from app.db.models import Base

# Drop the old users table if it exists
print("Checking existing schema...")
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Existing tables: {tables}")

if 'users' in tables:
    print("\nDropping old users table...")
    with engine.connect() as conn:
        # Drop dependent tables first
        for table in ['tutoring_sessions', 'exam_attempts', 'questions', 'study_materials', 'exams']:
            if table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"Dropped {table}")
        
        # Drop users table
        conn.execute(text("DROP TABLE users CASCADE"))
        conn.commit()
        print("Dropped users table")

# Create all tables based on models
print("\nCreating tables from models...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

# Verify new schema
inspector = inspect(engine)
users_columns = inspector.get_columns('users')
print("\nNew users table columns:")
for col in users_columns:
    print(f"  - {col['name']}: {col['type']}")
