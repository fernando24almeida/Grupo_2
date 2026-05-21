from sqlmodel import create_engine, text
import os
from dotenv import load_dotenv

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def check_all_tables():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [r[0] for r in res]
        print(f"Tabelas: {tables}")
        
        for table in tables:
            print(f"\n--- Colunas em '{table}' ---")
            res = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"))
            for r in res:
                print(f"  - {r[0]} ({r[1]})")

if __name__ == "__main__":
    check_all_tables()
