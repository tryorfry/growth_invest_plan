from src.database import Database
from sqlalchemy import text

db = Database("postgresql://postgres.qvhphaxtfduvnylqfrno:1@Something11@Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require")
db.init_db()

with db.get_session() as session:
    try:
        session.execute(text("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'dark';"))
        session.commit()
        print("Success! Migration complete.")
    except Exception as e:
        print(f"Failed or already run: {e}")
