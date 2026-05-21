from sqlalchemy import text, inspect
from sqlmodel import create_engine
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import configuracoes

def debug_columns():
    print(f"URL da BD: {configuracoes.DATABASE_URL.split('@')[-1]}")
    motor = create_engine(configuracoes.DATABASE_URL)
    
    inspetor = inspect(motor)
    tabelas = ["utente", "episodio_urgencia", "ato", "internamento"]
    
    for tabela in tabelas:
        print(f"\n--- Colunas em '{tabela}' ---")
        try:
            colunas = inspetor.get_columns(tabela)
            for c in colunas:
                print(f"  - {c['name']} ({c['type']})")
        except Exception as e:
            print(f"Erro ao ler tabela '{tabela}': {e}")

if __name__ == "__main__":
    debug_columns()
