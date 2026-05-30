import random
from sqlmodel import Session, create_engine, select
from app.models.models import (
    EpisodioUrgencia,
    Triagem,
    Ato,
    Internamento,
    Enfermeiro,
    Medico,
    FuncionarioHospital,
    Utilizador
)
from app.core.config import configuracoes

def corrigir_profissionais():
    engine = create_engine(configuracoes.DATABASE_URL)
    
    with Session(engine) as session:
        print("--- A iniciar correção de profissionais ausentes ---")
        
        # 1. Obter pools de profissionais válidos
        enfermeiros = session.exec(select(Enfermeiro)).all()
        medicos = session.exec(select(Medico)).all()
        
        # Rececionistas (Utilizadores vinculados a funcionários RECECIONISTA)
        rececionistas = session.exec(
            select(Utilizador).join(FuncionarioHospital, Utilizador.num_func == FuncionarioHospital.num_func)
            .where(FuncionarioHospital.tipo_func == "RECECIONISTA")
        ).all()
        
        if not rececionistas:
            # Fallback para qualquer admin ou utilizador se não houver rececionistas puros
            rececionistas = session.exec(select(Utilizador)).all()

        if not all([enfermeiros, medicos, rececionistas]):
            print("Erro: Não existem profissionais suficientes em todas as categorias na base de dados.")
            return

        # 2. Corrigir Episódios (Admissão)
        epis_sem_recep = session.exec(select(EpisodioUrgencia).where(EpisodioUrgencia.id_utilizador_rececao == None)).all()
        print(f"A corrigir {len(epis_sem_recep)} episódios sem rececionista...")
        for ep in epis_sem_recep:
            ep.id_utilizador_rececao = random.choice(rececionistas).id_utilizador
            session.add(ep)

        # 3. Corrigir Triagens
        triagens_sem_enf = session.exec(select(Triagem).where(Triagem.num_func_enfermeiro == None)).all()
        # Nota: num_func_enfermeiro pode ser NOT NULL no schema físico, 
        # mas verificamos por segurança se houver inconsistência no modelo.
        print(f"A verificar triagens...")
        # (Se o campo for NOT NULL, o len será 0, o que está correto)
        for t in triagens_sem_enf:
            t.num_func_enfermeiro = random.choice(enfermeiros).num_func
            session.add(t)

        # 4. Corrigir Atos Médicos
        atos_sem_med = session.exec(select(Ato).where(Ato.num_func == None)).all()
        print(f"A verificar atos médicos...")
        for a in atos_sem_med:
            a.num_func = random.choice(medicos).num_func
            session.add(a)

        # 5. Corrigir Internamentos (Médico Responsável)
        ints_sem_med = session.exec(select(Internamento).where(Internamento.num_func_medico == None)).all()
        print(f"A corrigir {len(ints_sem_med)} internamentos sem médico responsável...")
        for i in ints_sem_med:
            i.num_func_medico = random.choice(medicos).num_func
            session.add(i)

        session.commit()
        print("--- Correção concluída com sucesso ---")

if __name__ == "__main__":
    corrigir_profissionais()
