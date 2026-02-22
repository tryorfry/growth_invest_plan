import urllib.parse
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine

# Try passing the password strictly URL encoded instead of unquoted to the URL constructor
db_url = "postgresql://postgres.qvhphaxtfduvnylqfrno:1%40Something11%40Anything1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

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
        
        # KEY CHANGE: Let SQLAlchemy handle its own internal encoding, pass the raw literal 1@Something string to the URL object 
        # so it doesn't get double encoded by Psycopg2 over the wire to PgBouncer
        
        url_obj = URL.create(
            drivername=scheme,
            username=user,
            password=urllib.parse.unquote(pwd), # We pass the unquoted actual string "1@Something"
            host=host,
            port=port,
            database=db
        )

        connect_args = {
            "keepalives": 1, 
            "keepalives_idle": 30, 
            "keepalives_interval": 10, 
            "keepalives_count": 5,
            "sslmode": "require",
            # Add application name for PgBouncer routing
            "application_name": "growth_invest_plan"
        }
        
        print(f"Testing Engine Auth for User: {url_obj.username}")
        # print(f"Pwd being passed to adapter: {url_obj.password}")
        
        try:
            print("Trying engine connection...")
            engine = create_engine(url_obj, connect_args=connect_args)
            with engine.connect() as conn:
                print("Connection SUCCESS!")
        except Exception as e:
            print(f"Error: {e}")

