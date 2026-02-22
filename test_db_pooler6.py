import urllib.parse
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
import os

db_url = "postgresql://postgres.qvhphaxtfduvnylqfrno:1@Something11@Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

raw_url = db_url
if "://" in raw_url and "@" in raw_url:
    scheme_end = raw_url.find("://") + 3
    scheme = raw_url[:scheme_end - 3]
    rest = raw_url[scheme_end:]
    
    last_at = rest.rfind("@")
    creds = rest[:last_at]
    host_block = rest[last_at+1:]
    
    port = None
    db = None
    if "/" in host_block:
        host_port, db = host_block.split("/", 1)
    else:
        host_port = host_block
        
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        if port_str.isdigit():
            port = int(port_str)
    else:
        host = host_port

    if ":" in creds:
        user, pwd = creds.split(":", 1)
        
        # SOLUTION: Do not use URL.create dictionary because Psycopg2's dictionary parser strips domains from users.
        # Instead, rebuild the raw postgres string perfectly URL-encoded, and feed the ENCODED string directly to create_engine.
        # This forces psycopg2 to pass the exact characters we give it.

        encoded_pwd = urllib.parse.quote(urllib.parse.unquote(pwd), safe="")
        encoded_user = urllib.parse.quote(user, safe=".") 
        
        safe_url = f"{scheme}://{encoded_user}:{encoded_pwd}@{host}:{port}/{db}?sslmode=require"
        print(f"Constructed Safe URL: {safe_url}")

        connect_args = {
            "keepalives": 1, 
            "keepalives_idle": 30, 
            "keepalives_interval": 10, 
            "keepalives_count": 5
        }
        
        try:
            print("Trying engine connection...")
            engine = create_engine(safe_url, connect_args=connect_args)
            with engine.connect() as conn:
                print("Connection SUCCESS!")
        except Exception as e:
            print(f"Error: {e}")

