import os
import sys

# Add parent directory to path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from src.database import Database

def migrate():
    print("Starting migration to add user_id for multi-tenancy...")
    
    db = Database()
    
    with db.engine.connect() as conn:
        tables = ['watchlists', 'alerts', 'portfolios']
        for table in tables:
            try:
                # Add user_id column with default value of 1 (admin user)
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1 REFERENCES users(id)"))
                conn.commit()
                print(f"Successfully added user_id to {table}")
            except Exception as e:
                if 'duplicate column name' in str(e).lower():
                    print(f"Column user_id already exists in {table}")
                else:
                    print(f"Error migrating {table}: {e}")
                    
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
