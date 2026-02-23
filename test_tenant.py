from src.database import Database
from sqlalchemy import inspect
from dotenv import load_dotenv

load_dotenv()
db = Database()
inspector = inspect(db.engine)

for table in ['watchlists', 'portfolios', 'alerts']:
    try:
        cols = inspector.get_columns(table)
        print(f"--- {table} ---")
        for col in cols:
            print(col['name'])
    except Exception as e:
        print(f"Error on {table}: {e}")
