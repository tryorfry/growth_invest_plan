import urllib.parse
from sqlalchemy.engine.url import make_url

db_url_broken = "postgresql://postgres:1@Something11@Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"

try:
    url = make_url(db_url_broken)
    print(url)
except Exception as e:
    print(f"make_url failed: {e}")

