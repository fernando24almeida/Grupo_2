from sqlmodel import Session, create_engine, select
from app.models.models import Utilizador, FuncionarioHospital, Enfermeiro, Medico, Triagem

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
engine = create_engine(DATABASE_URL)

def debug_links():
    with Session(engine) as sessao:
        print("\n--- UTILIZADORES ---")
        users = sessao.exec(select(Utilizador)).all()
        for u in users:
            print(f"User: {u.nome_utilizador} | Nome: {u.nome_completo} | NumFunc: {u.num_func} | RoleID: {u.id_role}")
            
        print("\n--- FUNCIONÁRIOS ---")
        funcs = sessao.exec(select(FuncionarioHospital)).all()
        for f in funcs:
            print(f"Func: {f.num_func} | Tipo: {f.tipo_func}")
            
        print("\n--- ENFERMEIROS ---")
        enfs = sessao.exec(select(Enfermeiro)).all()
        for e in enfs:
            print(f"Enf: {e.num_func}")
            
        print("\n--- TRIAGENS ---")
        triagens = sessao.exec(select(Triagem)).all()
        for t in triagens:
            print(f"Triagem: {t.num_triagem} | Episódio: {t.cod_epis} | Enf: {t.num_func_enfermeiro}")

if __name__ == "__main__":
    debug_links()
