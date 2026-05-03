from sqlmodel import create_engine, Session, select
from app.models.models import Utilizador
from app.core.db import motor

with Session(motor) as session:
    users = session.exec(select(Utilizador)).all()
    print("\nLista de Utilizadores e Estado:")
    for u in users:
        print(f"Username: {u.nome_utilizador}")
        print(f"  - Ativo: {u.ativo}")
        print(f"  - MFA Ativo: {u.mfa_ativo}")
        print(f"  - MFA Secret: {'Configurado' if u.mfa_secret else 'Nao Configurado'}")
        print(f"  - ID Role: {u.id_role}")
        print("-" * 30)
