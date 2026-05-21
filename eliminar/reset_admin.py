from sqlmodel import Session, select
from backend.app.core.db import motor
from backend.app.models.models import Utilizador
from backend.app.core.security import obter_hash_palavra_passe

def reset_admin_password():
    with Session(motor) as sessao:
        admin = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == "admin")).first()
        if admin:
            admin.hash_palavra_passe = obter_hash_palavra_passe("admin123")
            admin.ativo = True
            sessao.add(admin)
            sessao.commit()
            print("Admin password reset to admin123 and activated.")
        else:
            print("Admin user not found.")

if __name__ == "__main__":
    reset_admin_password()
