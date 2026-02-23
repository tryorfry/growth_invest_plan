from sqlalchemy import create_engine, inspect
from sqlalchemy import text

db_url = "postgresql://postgres.qvhphaxtfduvnylqfrno:1%40Something11%40Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        print("Connected successfully!")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables: {tables}")
        
        if 'portfolios' in tables:
            cols = [col['name'] for col in inspector.get_columns('portfolios')]
            print(f"Columns in portfolios: {cols}")
            
            if 'initial_balance' not in cols:
                print("Missing initial_balance, attempting migration...")
                # We'll try to add it
                conn.execute(text("ALTER TABLE portfolios ADD COLUMN initial_balance FLOAT"))
                conn.commit()
                print("Migration complete!")
                
except Exception as e:
    print(f"Error: {e}")
