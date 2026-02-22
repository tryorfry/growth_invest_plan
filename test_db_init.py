from src.database import Database
print("Initializing database connection...")
db = Database()
print(f"URL: {db.db_url}")
try:
    print("Executing create_all()...")
    db.init_db()
    print("Database initialization successful!")
except Exception as e:
    import traceback
    print("Initialization failed with:")
    traceback.print_exc()
