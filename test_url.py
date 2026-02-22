import urllib.parse

db_url = "postgresql://postgres:1@Something11@Anything1@db.qvhphaxtfduvnylqfrno.supabase.co:5432/postgres"

if "://" in db_url:
    scheme, rest = db_url.split("://", 1)
    if "@" in rest:
        parts = rest.rsplit("@", 1)
        creds = parts[0]
        host_port_db = parts[1]
        
        if "@" in creds or ":" in creds:
            if ":" in creds:
                user, pwd = creds.split(":", 1)
                
                # Try unquoting first in case they already partially encoded it
                pwd = urllib.parse.unquote(pwd)
                encoded_pwd = urllib.parse.quote(pwd)
                db_url = f"{scheme}://{user}:{encoded_pwd}@{host_port_db}"

print(db_url)
