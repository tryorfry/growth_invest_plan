import urllib.parse
from sqlalchemy.engine.url import URL

db_url = "postgresql://postgres.qvhphaxtfduvnylqfrno:1@Something11@Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

raw_url = db_url
if "://" in raw_url and "@" in raw_url:
    scheme_end = raw_url.find("://") + 3
    scheme = raw_url[:scheme_end - 3]
    rest = raw_url[scheme_end:]
    
    last_at = rest.rfind("@")
    creds = rest[:last_at]
    host_block = rest[last_at+1:]
    
    if ":" in creds:
        user, pwd = creds.split(":", 1)
        pwd_unquoted = urllib.parse.unquote(pwd)
        
        print(f"Extracted User: '{user}'")
        print(f"Extracted Pass: '{pwd_unquoted}'")

