from sqlalchemy import text
from sqlmodel import create_engine, Session, select
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import configuracoes
from app.models.models import Utente

def reproduce():
    print(f"URL: {configuracoes.DATABASE_URL.split('@')[-1]}")
    motor = create_engine(configuracoes.DATABASE_URL)
    
    with Session(motor) as sessao:
        try:
            print("Tentando: sessao.exec(select(Utente)).first()...")
            # Esta é a linha 51 do db.py que falhou no log do utilizador
            res = sessao.exec(select(Utente)).first()
            print("Sucesso! Utente obtido:", res.nome if res else "Nenhum utente na BD")
        except Exception as e:
            print(f"\n[FALHA REPRODUZIDA] Erro: {e}")
            
            print("\nTentando query SQL manual para confirmar colunas...")
            with motor.connect() as conn:
                res = conn.execute(text("SELECT * FROM utente LIMIT 0;"))
                print("Colunas detectadas via SQL:", res.keys())

if __name__ == "__main__":
    reproduce()
