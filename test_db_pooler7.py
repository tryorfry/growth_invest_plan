import psycopg2

try:
    print("Trying raw psycopg2 connection pooler login...")
    # Using strictly the params Supabase documentation provides for IPv4 pooler
    conn = psycopg2.connect(
        host="aws-1-ap-southeast-1.pooler.supabase.com",
        port=6543,
        user="postgres.qvhphaxtfduvnylqfrno",
        password="1@Something11@Anything1",
        dbname="postgres",
        sslmode="require"
    )
    print("Direct Psycopg2 Connection SUCCESS!")
    conn.close()
except Exception as e:
    print(f"Direct connection failed: {e}")
