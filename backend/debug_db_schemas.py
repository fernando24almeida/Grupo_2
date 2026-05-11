from sqlalchemy import text, inspect
from sqlmodel import create_engine
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import configuracoes

def debug_schemas():
    motor = create_engine(configuracoes.DATABASE_URL)
    inspetor = inspect(motor)
    
    schemas = inspetor.get_schema_names()
    print(f"Schemas encontrados: {schemas}")
    
    for schema in schemas:
        tabelas = inspetor.get_table_names(schema=schema)
        if "utente" in tabelas:
            print(f"\nTabela 'utente' encontrada no schema: {schema}")
            colunas = inspetor.get_columns("utente", schema=schema)
            for c in colunas:
                print(f"  - {c['name']} ({c['type']})")

if __name__ == "__main__":
    debug_schemas()
