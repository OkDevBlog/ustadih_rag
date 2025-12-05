from sqlalchemy import inspect, text
from app.db.session import engine

# Check columns in users table
inspector = inspect(engine)
columns = inspector.get_columns('users')

print("Columns in users table:")
for col in columns:
    print(f"  - {col['name']}: {col['type']}")

# Check if hashed_password and updated_at exist
col_names = [c['name'] for c in columns]
has_hashed_password = 'hashed_password' in col_names
has_updated_at = 'updated_at' in col_names

print(f"\nhashed_password exists: {has_hashed_password}")
print(f"updated_at exists: {has_updated_at}")

if not has_hashed_password or not has_updated_at:
    print("\nNeed to add missing columns...")
    # Add the columns if missing
    with engine.connect() as conn:
        if not has_hashed_password:
            conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)"))
            conn.commit()
            print("Added hashed_password column")
        
        if not has_updated_at:
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            conn.commit()
            print("Added updated_at column")
