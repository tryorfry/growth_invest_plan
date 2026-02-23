from src.database import Database
from dotenv import load_dotenv
import os

load_dotenv()
print("RAW ENV:", os.getenv("DATABASE_URL"))
db = Database()
print("PARSED URL:", db.db_url)
print("PARSED USER:", getattr(db.db_url, "username", None))
