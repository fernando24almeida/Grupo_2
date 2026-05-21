from app.core.db import motor
from app.models.models import Utente
from sqlmodel import Session, select

def check_utente():
    num = 111122223
    with Session(motor) as sessao:
        utente = sessao.get(Utente, num)
        if utente:
            print(f"Utente {num} encontrado!")
            print(f"Nome: {utente.nome}")
            print(f"Ativo: {utente.ativo}")
            print(f"Password Hash: {utente.password_hash[:15] if utente.password_hash else 'Nenhum'}")
            print(f"ID Role: {utente.id_role}")
        else:
            print(f"Utente {num} NÃO encontrado.")
            # List some utentes to see what we have
            all_u = sessao.exec(select(Utente).limit(5)).all()
            print("Alguns utentes na BD:")
            for u in all_u:
                print(f"- {u.num_utente}: {u.nome}")

if __name__ == "__main__":
    check_utente()
