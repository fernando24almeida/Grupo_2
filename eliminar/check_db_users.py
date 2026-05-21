from sqlmodel import Session, select
from backend.app.core.db import motor
from backend.app.models.models import Utilizador

def check_admin():
    with Session(motor) as sessao:
        admin = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == "admin")).first()
        if admin:
            print(f"Found admin: {admin.nome_utilizador}, ID: {admin.id_utilizador}, Email: {admin.email}")
        else:
            print("Admin NOT found by nome_utilizador='admin'")
            
        all_users = sessao.exec(select(Utilizador)).all()
        print("\nAll users:")
        for u in all_users:
            print(f"- {u.nome_utilizador} (ID: {u.id_utilizador})")

if __name__ == "__main__":
    check_admin()
