import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres.cgcqhgjusfxwqqcnslgl:AbhishekChaudhary30@aws-0-ap-south-1.pooler.supabase.com:6543/postgres')
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    print(cur.fetchall())
except Exception as e:
    print('ERROR:', e)
