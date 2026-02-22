from sqlalchemy import create_engine, inspect
import urllib.parse
from sqlalchemy.engine.url import URL

db_url = "postgresql://postgres.qvhphaxtfduvnylqfrno:1@Something11@Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

raw_url = db_url
scheme_end = raw_url.find("://") + 3
scheme = raw_url[:scheme_end - 3]
rest = raw_url[scheme_end:]
last_at = rest.rfind("@")
creds = rest[:last_at]
host_block = rest[last_at+1:]
host_port, db = host_block.split("/", 1)
host, port_str = host_port.split(":", 1)
port = int(port_str)
user, pwd = creds.split(":", 1)

encoded_pwd = urllib.parse.quote(urllib.parse.unquote(pwd), safe="")
encoded_user = urllib.parse.quote(user, safe=".") 
safe_url = f"{scheme}://{encoded_user}:{encoded_pwd}@{host}:{port}/{db}?sslmode=require"

engine = create_engine(safe_url)

inspector = inspect(engine)
columns = inspector.get_columns("analyses")
print("Columns in 'analyses' table:")
for c in columns:
    print(f"- {c['name']} ({c['type']})")
    
