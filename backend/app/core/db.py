from sqlmodel import create_engine, Session, SQLModel, select
from datetime import date
from .config import configuracoes
from ..models.models import PapelUtilizador, Utilizador, Hospital, Utente, FuncionarioHospital, Enfermeiro, Medico
from .security import obter_hash_palavra_passe

motor = create_engine(configuracoes.DATABASE_URL)

def obter_sessao():
    with Session(motor) as sessao:
        yield sessao

def inicializar_bd():
    SQLModel.metadata.create_all(motor)
    
    with Session(motor) as sessao:
        # Check if hospitals exist
        hosp_existente = sessao.exec(select(Hospital)).first()
        if not hosp_existente:
            hosp = Hospital(nome_hosp="Hospital Central de Urgências", local_hosp="Lisboa")
            sessao.add(hosp)
            sessao.commit()
            
        # Check if utentes exist
        utente_existente = sessao.exec(select(Utente)).first()
        if not utente_existente:
            ut = Utente(
                num_utente=123456789, 
                nome="João Silva Exemplo", 
                telemovel="912345678",
                sexo="M", 
                localidade="Lisboa", 
                data_nascimento=date(1994, 1, 1)
            )
            sessao.add(ut)
            sessao.commit()

        # Check if roles exist
        papeis_existentes = sessao.exec(select(PapelUtilizador)).first()
        if not papeis_existentes:
            papeis = [
                PapelUtilizador(nome="ADMIN"),
                PapelUtilizador(nome="MEDICO"),
                PapelUtilizador(nome="ENFERMEIRO"),
                PapelUtilizador(nome="RECECIONISTA"),
                PapelUtilizador(nome="TECNICO")
            ]
            sessao.add_all(papeis)
            sessao.commit()
            
        # Create initial staff for testing
        enfermeiro_existente = sessao.exec(select(Enfermeiro)).first()
        if not enfermeiro_existente:
            f1 = FuncionarioHospital(num_func=1001, sexo="F", tipo_func="ENFERMEIRO")
            sessao.add(f1)
            sessao.commit()
            e1 = Enfermeiro(num_func=1001)
            sessao.add(e1)
            sessao.commit()

        medico_existente = sessao.exec(select(Medico)).first()
        if not medico_existente:
            f2 = FuncionarioHospital(num_func=1002, sexo="M", tipo_func="MEDICO")
            sessao.add(f2)
            sessao.commit()
            m1 = Medico(num_func=1002, estagiario="NÃO")
            sessao.add(m1)
            sessao.commit()

        # Create initial admin user
        utilizador_admin = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == "admin")).first()
        if not utilizador_admin:
            papel_admin = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == "ADMIN")).one()
            utilizador = Utilizador(
                nome_utilizador="admin",
                nome_completo="Administrador do Sistema",
                email="admin@sistema.pt",
                hash_palavra_passe=obter_hash_palavra_passe("admin123"),
                id_role=papel_admin.id_role,
                ativo=True
            )
            sessao.add(utilizador)
            sessao.commit()
