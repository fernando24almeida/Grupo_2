from sqlmodel import Session, create_engine, select
from app.models.models import Utente
import os

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def check_utente():
    with Session(engine) as session:
        statement = select(Utente).where(Utente.num_utente == 111111111)
        utente = session.exec(statement).first()
        if utente:
            print(f"Utente encontrado: {utente.nome}, Num: {utente.num_utente}")
        else:
            print("Utente 111111111 NÃO encontrado na base de dados.")
            
        # Listar todos para ver o que temos
        print("\nLista de todos os utentes:")
        all_utentes = session.exec(select(Utente)).all()
        for u in all_utentes:
            print(f"- {u.nome} ({u.num_utente})")

if __name__ == "__main__":
    check_utente()
