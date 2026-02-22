from src.database import Database
import os

os.environ["DATABASE_URL"] = "postgresql://postgres:1%40Something11%40Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"

print("Initializing Supabase connection...")
db = Database()
print(f"URL Object Type: {type(db.db_url)}")
print(f"URL: {db.db_url}")

try:
    print("Executing create_all()...")
    db.init_db()
    print("Database initialization successful!")
except Exception as e:
    import traceback
    print("Initialization failed with:")
    traceback.print_exc()
