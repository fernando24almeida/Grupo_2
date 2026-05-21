from sqlmodel import Session, create_engine, select
from app.models.models import Utilizador, FuncionarioHospital, PapelUtilizador
import os

DATABASE_URL = "postgresql://postgres:admin@127.0.0.1:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def check_mapping():
    with Session(engine) as session:
        print("--- Utilizadores ---")
        users = session.exec(select(Utilizador)).all()
        for u in users:
            papel = session.get(PapelUtilizador, u.id_role)
            print(f"ID: {u.id_utilizador} | Username: {u.nome_utilizador} | Nome: {u.nome_completo} | NumFunc: {u.num_func} | Role: {papel.nome if papel else 'NONE'}")
            
        print("\n--- Funcionários Hospital ---")
        profs = session.exec(select(FuncionarioHospital)).all()
        for f in profs:
            print(f"NumFunc: {f.num_func} | Tipo: {f.tipo_func}")

if __name__ == "__main__":
    check_mapping()
