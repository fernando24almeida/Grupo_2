from sqlmodel import create_engine, Session, SQLModel, select
from datetime import date
from .config import configuracoes
from ..models.models import PapelUtilizador, Utilizador, Hospital, Utente, FuncionarioHospital, Enfermeiro, Medico, ServicoHospitalar
from .security import obter_hash_palavra_passe
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tentar extrair o host para logar (sem mostrar a password)
db_url = configuracoes.DATABASE_URL
try:
    if "@" in db_url:
        host_info = db_url.split("@")[1]
        logger.info(f"[DB] A tentar ligar à base de dados em: {host_info}")
    else:
        logger.info("[DB] A tentar ligar à base de dados (URL sem formato padrão)")
except:
    logger.info("[DB] A tentar ligar à base de dados...")

motor = create_engine(
    configuracoes.DATABASE_URL,
    pool_pre_ping=True  # Verifica a conexão antes de usar (útil em produção como Render)
)

def obter_sessao():
    with Session(motor) as sessao:
        yield sessao

def inicializar_bd():
    try:
        # 1. Tenta criar as tabelas base
        SQLModel.metadata.create_all(motor)
        
        # 2. Migrações automáticas (Self-healing)
        # Adiciona colunas que podem estar em falta em instalações existentes
        from sqlalchemy import text
        colunas_necessarias = [
            ("utente", "parentesco", "VARCHAR(100)"),
            ("utente", "id_role", "INT REFERENCES role(id_role)"),
            ("episodio_urgencia", "id_utilizador_rececao", "INT REFERENCES utilizador(id_utilizador)"),
            ("ato", "diagnostico", "TEXT"),
            ("ato", "notas_clinicas", "TEXT"),
            ("ato", "exame_fisico", "TEXT"),
            ("ato", "decisao_clinica", "VARCHAR(50)"),
            ("internamento", "num_func_medico", "INT REFERENCES medico(num_func)")
        ]
        
        with motor.connect() as conn:
            for tabela, coluna, tipo in colunas_necessarias:
                try:
                    # Verificar se a coluna existe
                    check = conn.execute(text(f"SELECT count(*) FROM information_schema.columns WHERE table_name='{tabela}' AND column_name='{coluna}';")).scalar()
                    if check == 0:
                        print(f"[MIGRATE] Adicionando coluna '{coluna}' à tabela '{tabela}'...")
                        conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo};"))
                        conn.commit()
                except Exception as me:
                    print(f"[MIGRATE ERROR] Falha ao adicionar {tabela}.{coluna}: {me}")
            
            # Remover unique do email se existir
            try:
                conn.execute(text("ALTER TABLE utente DROP CONSTRAINT IF EXISTS utente_email_key;"))
                conn.commit()
            except: pass

        print("[SUCCESS] Base de dados inicializada e migrada com sucesso.")
    except Exception as e:
        print(f"[ERROR] Erro ao ligar à base de dados: {e}")
        raise e
    
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
                email="joao@exemplo.pt",
                telemovel="912345678",
                sexo="M", 
                localidade="Lisboa", 
                data_nascimento=date(1994, 1, 1)
            )
            sessao.add(ut)
            
            # Adicionar utente para o teste de API
            ut_teste = Utente(
                num_utente=111111111,
                nome="Utente de Teste API",
                email="teste_api@exemplo.pt",
                telemovel="999999999",
                sexo="M",
                localidade="Teste",
                data_nascimento=date(1990, 1, 1)
            )
            sessao.add(ut_teste)
            sessao.commit()

        # Check if roles exist
        papeis_existentes = sessao.exec(select(PapelUtilizador)).first()
        if not papeis_existentes:
            papeis = [
                PapelUtilizador(nome="ADMIN"),
                PapelUtilizador(nome="MEDICO"),
                PapelUtilizador(nome="ENFERMEIRO"),
                PapelUtilizador(nome="RECECIONISTA"),
                PapelUtilizador(nome="TECNICO"),
                PapelUtilizador(nome="UTENTE")
            ]
            sessao.add_all(papeis)
            sessao.commit()
        else:
            # Garantir que o papel UTENTE existe mesmo que outros já existam
            utente_role = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == "UTENTE")).first()
            if not utente_role:
                sessao.add(PapelUtilizador(nome="UTENTE"))
                sessao.commit()
            
        # Atribuir id_role UTENTE a todos os utentes que não têm
        papel_utente = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == "UTENTE")).one()
        utentes_sem_role = sessao.exec(select(Utente).where(Utente.id_role == None)).all()
        for u in utentes_sem_role:
            u.id_role = papel_utente.id_role
            sessao.add(u)
        if utentes_sem_role:
            sessao.commit()
            print(f"[SUCCESS] Atribuído papel UTENTE a {len(utentes_sem_role)} utentes.")
            
        # Check if services exist
        servicos_existentes = sessao.exec(select(ServicoHospitalar)).first()
        if not servicos_existentes:
            hosp_nome = "Hospital Central de Urgências"
            servicos = [
                ServicoHospitalar(nome="Medicina Interna", id_hosp=hosp_nome),
                ServicoHospitalar(nome="Cirurgia Geral", id_hosp=hosp_nome),
                ServicoHospitalar(nome="Ortopedia", id_hosp=hosp_nome),
                ServicoHospitalar(nome="Cardiologia", id_hosp=hosp_nome),
                ServicoHospitalar(nome="Pediatria", id_hosp=hosp_nome)
            ]
            sessao.add_all(servicos)
            
            # Adicionar também para o hospital de teste se existir
            hosp_teste = sessao.exec(select(Hospital).where(Hospital.nome_hosp == "Centro Hospitalar TESTE")).first()
            if hosp_teste:
                servicos_teste = [
                    ServicoHospitalar(nome="Unidade de Cuidados Intensivos", id_hosp=hosp_teste.nome_hosp),
                    ServicoHospitalar(nome="Neurologia", id_hosp=hosp_teste.nome_hosp)
                ]
                sessao.add_all(servicos_teste)
            
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
