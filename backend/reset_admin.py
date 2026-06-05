# backend/reset_admin.py
from sqlmodel import Session, select
from app.core.db import motor
from app.models.models import Utilizador
from app.core.security import obter_hash_palavra_passe

with Session(motor) as sessao:
    admin = sessao.exec(
        select(Utilizador).where(Utilizador.nome_utilizador == "admin")
    ).first()

    if not admin:
        print("Admin não encontrado.")
    else:
        admin.hash_palavra_passe = obter_hash_palavra_passe("admin123")
        admin.ativo = True
        admin.mfa_ativo = False
        admin.mfa_secret = None
        sessao.add(admin)
        sessao.commit()
        print("Password do admin reposta para admin123")