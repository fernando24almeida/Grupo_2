import psycopg2
import sys

users = ["postgres", "admin", "postgres_user"]
passwords = ["admin", "123456", "admin123", "postgres", "root", "123", "password"]
database = "postgres"
host = "127.0.0.1"
port = "5432"

for user in users:
    for pw in passwords:
        try:
            print(f"Trying {user}:{pw}")
            conn = psycopg2.connect(
                dbname=database,
                user=user,
                password=pw,
                host=host,
                port=port
            )
            print(f"Success! {user}:{pw}")
            conn.close()
            sys.exit(0)
        except Exception as e:
            # print(f"Failed {user}:{pw}: {e}")
            pass

print("All failed.")
sys.exit(1)
