import os
import urllib.parse
from sqlalchemy.engine.url import make_url

url_env = os.environ.get("DATABASE_URL")
print("ENV URL:", url_env)

try:
    if url_env:
        parsed = make_url(url_env)
        print("Parsed from ENV:", parsed)
except Exception as e:
    print("ENV parse error:", e)

