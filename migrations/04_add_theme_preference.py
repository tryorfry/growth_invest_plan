import os
from sqlalchemy import create_engine, text

def run_migration():
    """Add theme_preference column to users table if it doesn't exist"""
    print("Starting database migration: Add theme_preference to users...")
    
    # Supabase Production PostgreSQL URL
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set in environment.")
        return
        
    try:
        engine = create_engine(db_url)
        with engine.begin() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='theme_preference';
            """)).fetchone()
            
            if not result:
                print("Column 'theme_preference' not found. Adding...")
                conn.execute(text("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'dark';"))
                print("Successfully added theme_preference.")
            else:
                print("Column 'theme_preference' already exists. Skipping.")
                
        print("Migration complete!")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
