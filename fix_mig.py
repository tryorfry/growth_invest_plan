import os
import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote_plus("1@Something11@Anything1")
url = f"postgresql://postgres.qvhphaxtfduvnylqfrno:{password}@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(url)
with engine.begin() as conn:
    print("Executing ALTER TABLE...")
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'dark';"))
        print("Success!")
    except Exception as e:
        print("Error:", e)
