import psycopg2
import sys

passwords = ["admin", "123456", "admin123", "postgres", "root", "123", ""]
database = "postgres"
user = "postgres"
host = "127.0.0.1"
port = "5432"

for pw in passwords:
    try:
        print(f"Trying password: {pw}")
        conn = psycopg2.connect(
            dbname=database,
            user=user,
            password=pw,
            host=host,
            port=port
        )
        print(f"Success! Password for user '{user}' is '{pw}'")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"Failed with password '{pw}': {e}")

sys.exit(1)
