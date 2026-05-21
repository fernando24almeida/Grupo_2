from sqlmodel import Session, create_engine, select
from app.models.models import Utente
from app.api.clinical import UtenteCreate, criar_utente
from fastapi import HTTPException, BackgroundTasks
import os

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

class MockBackgroundTasks:
    def add_task(self, func, *args, **kwargs):
        pass

def test_criar_utente():
    with Session(engine) as session:
        dados = UtenteCreate(
            num_utente=777777777,
            nome="Teste Erro",
            email="erro@teste.pt",
            sexo="M"
        )
        
        # Cleanup if exists
        u = session.get(Utente, 777777777)
        if u:
            session.delete(u)
            session.commit()

        print("Chamando criar_utente...")
        try:
            res = criar_utente(dados, MockBackgroundTasks(), session)
            print(f"Resultado: {res}")
            # If we were running under FastAPI, this 'res' would be filtered by response_model.
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    test_criar_utente()
