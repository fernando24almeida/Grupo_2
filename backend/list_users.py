from sqlmodel import create_engine, Session, select
import sys
import os

# Add the app directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'app'))

try:
    from app.core.config import configuracoes
    from app.models.models import Utilizador, PapelUtilizador

    motor = create_engine(configuracoes.DATABASE_URL)

    with Session(motor) as sessao:
        utilizadores = sessao.exec(select(Utilizador)).all()
        print(f"Encontrados {len(utilizadores)} utilizadores:")
        for utilizador in utilizadores:
            papel = sessao.get(PapelUtilizador, utilizador.id_papel)
            print(f"- ID: {utilizador.id}, Nome: {utilizador.nome_utilizador}, Papel: {papel.nome if papel else 'Desconhecido'}")
            
except Exception as e:
    print(f"Error: {e}")
