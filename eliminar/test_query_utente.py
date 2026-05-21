from sqlalchemy import text
from sqlmodel import create_engine
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import configuracoes

def test_query():
    print(f"URL: {configuracoes.DATABASE_URL.split('@')[-1]}")
    motor = create_engine(configuracoes.DATABASE_URL)
    
    with motor.connect() as conexao:
        try:
            print("Executando SELECT * FROM utente LIMIT 1...")
            res = conexao.execute(text("SELECT * FROM utente LIMIT 1;"))
            print("Colunas retornadas:", res.keys())
            row = res.fetchone()
            print("Dados da primeira linha:", row)
        except Exception as e:
            print(f"Erro ao executar query: {e}")

if __name__ == "__main__":
    test_query()
