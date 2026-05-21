from sqlmodel import Session, create_engine, select
from app.models.models import Utilizador, FuncionarioHospital, Enfermeiro, Medico, Triagem, Ato

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def debug_links():
    with Session(engine) as sessao:
        print("\n--- ATOS ---")
        atos = sessao.exec(select(Ato)).all()
        for a in atos:
            print(f"Ato: {a.id_ato} | Tipo: {a.tipo} | Func: {a.num_func}")
            
        print("\n--- UTILIZADORES COM NUM_FUNC ---")
        users = sessao.exec(select(Utilizador).where(Utilizador.num_func != None)).all()
        for u in users:
            print(f"User: {u.nome_utilizador} | Nome: {u.nome_completo} | NumFunc: {u.num_func}")

if __name__ == "__main__":
    debug_links()
