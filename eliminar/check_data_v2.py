from sqlmodel import Session, create_engine, select
from app.models.models import Triagem, Ato, Utilizador
import os

DATABASE_URL = "postgresql://postgres:admin@127.0.0.1:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def check_data():
    with Session(engine) as session:
        print("--- Triagens ---")
        triagens = session.exec(select(Triagem).limit(5)).all()
        for t in triagens:
            print(f"Episodio: {t.cod_epis} | NumFuncEnfermeiro: {t.num_func_enfermeiro}")
            user = session.exec(select(Utilizador).where(Utilizador.num_func == t.num_func_enfermeiro)).first()
            if user:
                print(f"  -> Match User: {user.nome_completo}")
            else:
                user_by_id = session.get(Utilizador, t.num_func_enfermeiro)
                if user_by_id:
                    print(f"  -> Match User by ID instead of NumFunc: {user_by_id.nome_completo}")
                else:
                    print("  -> No match in Utilizador table")

        print("\n--- Atos ---")
        atos = session.exec(select(Ato).limit(5)).all()
        for a in atos:
            print(f"Episodio: {a.cod_epis} | NumFunc: {a.num_func}")
            user = session.exec(select(Utilizador).where(Utilizador.num_func == a.num_func)).first()
            if user:
                print(f"  -> Match User: {user.nome_completo}")
            else:
                user_by_id = session.get(Utilizador, a.num_func)
                if user_by_id:
                    print(f"  -> Match User by ID instead of NumFunc: {user_by_id.nome_completo}")
                else:
                    print("  -> No match in Utilizador table")

if __name__ == "__main__":
    check_data()
