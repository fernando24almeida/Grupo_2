import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="postgres",
        user="postgres",
        password="admin"
    )
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Error type: {type(e)}")
    print(f"Error message: {e}")
    if hasattr(e, 'diag'):
        diag = e.diag
        print(f"Severity: {diag.severity}")
        print(f"SQLState: {diag.sqlstate}")
        print(f"Message Primary: {diag.message_primary}")
        print(f"Message Detail: {diag.message_detail}")
        print(f"Message Hint: {diag.message_hint}")
