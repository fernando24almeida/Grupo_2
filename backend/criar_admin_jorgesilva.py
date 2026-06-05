from sqlmodel import Session, select
from app.core.db import motor
from app.models.models import Utilizador, PapelUtilizador
from app.core.security import obter_hash_palavra_passe

with Session(motor) as sessao:
    # Verificar se o utilizador já existe
    existente = sessao.exec(
        select(Utilizador).where(Utilizador.nome_utilizador == "JorgeSilva")
    ).first()

    if existente:
        print("Utilizador 'JorgeSilva' já existe.")
    else:
        papel_admin = sessao.exec(
            select(PapelUtilizador).where(PapelUtilizador.nome == "ADMIN")
        ).first()

        if not papel_admin:
            print("Papel ADMIN não encontrado na base de dados.")
        else:
            novo_admin = Utilizador(
                nome_utilizador="JorgeSilva",
                nome_completo="Jorge Silva",
                email="jorgesilva@sistema.pt",
                hash_palavra_passe=obter_hash_palavra_passe("Hospital#2026!"),
                id_role=papel_admin.id_role,
                ativo=True,
                mfa_ativo=False
            )
            sessao.add(novo_admin)
            sessao.commit()
            print("Utilizador 'JorgeSilva' criado com sucesso com perfil ADMIN.")
