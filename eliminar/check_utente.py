from app.core.db import motor
from app.models.models import Utente
from sqlmodel import Session, select

def check():
    with Session(motor) as sessao:
        num = 226293300
        utente = sessao.get(Utente, num)
        if utente:
            print(f"SUCESSO: Utente {num} encontrado!")
            print(f"Nome: {utente.nome}")
            print(f"Ativo: {utente.ativo}")
        else:
            print(f"ERRO: Utente {num} NÃO encontrado na base de dados!")
            all_utentes = sessao.exec(select(Utente)).all()
            print(f"Total de utentes na BD: {len(all_utentes)}")
            if all_utentes:
                print(f"Exemplo de utente: {all_utentes[0].num_utente}")

if __name__ == "__main__":
    check()
