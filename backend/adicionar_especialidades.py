from sqlmodel import Session, create_engine, select
from app.models.models import Hospital, ServicoHospitalar
from app.core.config import configuracoes

def adicionar_especialidades():
    engine = create_engine(configuracoes.DATABASE_URL)
    novas_especialidades = ["Ginecologia", "Urologia", "Oftalmologia"]
    
    with Session(engine) as session:
        hospitais = session.exec(select(Hospital)).all()
        if not hospitais:
            print("Nenhum hospital encontrado.")
            return

        total_adicionado = 0
        for hosp in hospitais:
            for nome_esp in novas_especialidades:
                # Verificar se já existe
                existente = session.exec(
                    select(ServicoHospitalar).where(
                        ServicoHospitalar.nome == nome_esp,
                        ServicoHospitalar.id_hosp == hosp.nome_hosp
                    )
                ).first()
                
                if not existente:
                    novo_servico = ServicoHospitalar(nome=nome_esp, id_hosp=hosp.nome_hosp)
                    session.add(novo_servico)
                    total_adicionado += 1
        
        session.commit()
        print(f"Sucesso: Adicionadas {total_adicionado} novas especialidades no total.")

if __name__ == "__main__":
    adicionar_especialidades()
