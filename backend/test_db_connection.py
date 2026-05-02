from sqlmodel import create_engine, Session, select
import sys
import os

# Add the app directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'app'))

try:
    from app.core.config import configuracoes
    from app.models.models import Utilizador, PapelUtilizador
    from app.core.security import verificar_palavra_passe

    print(f"A ligar a: {configuracoes.DATABASE_URL}")
    motor = create_engine(configuracoes.DATABASE_URL)

    with Session(motor) as sessao:
        # Check if admin user exists
        utilizador_admin = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == "admin")).first()
        if utilizador_admin:
            print(f"Utilizador admin encontrado! ID: {utilizador_admin.id_utilizador}, Nome: {utilizador_admin.nome_utilizador}")
            
            # Test password
            pw_teste = "admin123"
            if verificar_palavra_passe(pw_teste, utilizador_admin.hash_palavra_passe):
                print(f"A palavra-passe '{pw_teste}' está CORRETA.")
            else:
                print(f"A palavra-passe '{pw_teste}' está ERRADA.")
        else:
            print("Utilizador admin NÃO encontrado.")
            
except Exception as e:
    print(f"Error: {e}")
