from sqlmodel import Session, create_engine, SQLModel, select
from .config import configuracoes
from ..models.models import PapelUtilizador, Hospital, FuncionarioHospital, Utilizador

# =============================================================================
# CONEXÃO COM A BASE DE DADOS
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro é a "ponte" entre o Python e o PostgreSQL. Ele cria a ligação 
# (engine) e tem funções para abrir e fechar sessões (pedidos) à base de dados.
# Também tem um papel importante no início: cria as tabelas e os dados base.
# =============================================================================

# Cria o motor de ligação usando o URL das configurações
engine = create_engine(configuracoes.DATABASE_URL)

def inicializar_bd():
<<<<<<< HEAD
    """ 
    Garante que a base de dados tem as tabelas criadas e os dados 
    iniciais (como o Administrador e os Cargos) para o sistema funcionar.
    """
    import logging
    logger = logging.getLogger("uvicorn.error")
=======
    try:
        # 1. Tenta criar as tabelas base
        SQLModel.metadata.create_all(motor)
        
        # 2. Migrações automáticas (Self-healing)
        # Adiciona colunas que podem estar em falta em instalações existentes
        from sqlalchemy import text
        colunas_necessarias = [
            ("utente", "parentesco", "VARCHAR(100)"),
            ("utente", "id_role", "INT REFERENCES role(id_role)"),
            ("utente", "role_name", "VARCHAR(100)"),
            ("utilizador", "role_name", "VARCHAR(100)"),
            ("medico", "especialidade", "VARCHAR(100)"),
            ("medico", "estagiario", "VARCHAR(10)"),
            ("episodio_urgencia", "id_utilizador_rececao", "INT REFERENCES utilizador(id_utilizador)"),
            ("episodio_urgencia", "sintomas", "TEXT"),
            ("episodio_urgencia", "observacoes", "TEXT"),
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
>>>>>>> 755ba7b546f82761405dac367cee876e346ab523
    
    # Importamos aqui dentro para evitar que o Python entre num círculo sem fim
    # (Circular Import) com o ficheiro de segurança.
    from .security import obter_hash_palavra_passe

    try:
        logger.info("A iniciar criação de tabelas...")
        SQLModel.metadata.create_all(engine)
        logger.info("Tabelas criadas ou já existentes.")
        
        with Session(engine) as sessao:
            # 1. Criar os Cargos (Roles) se não existirem
            logger.info("A verificar papeis...")
            papeis = ["ADMIN", "MEDICO", "ENFERMEIRO", "RECECIONISTA", "UTENTE"]
            for nome_papel in papeis:
                existe = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == nome_papel)).first()
                if not existe:
                    sessao.add(PapelUtilizador(nome=nome_papel))
            
            # 2. Criar Hospital Principal
            logger.info("A verificar hospital...")
            hosp_nome = "Hospital Central de Urgências"
            existe_hosp = sessao.get(Hospital, hosp_nome)
            if not existe_hosp:
                sessao.add(Hospital(nome_hosp=hosp_nome, local_hosp="Lisboa"))
                
            # 3. Criar Utilizador Administrador Padrão (admin123/admin123)
            logger.info("A verificar administrador padrão...")
            admin_username = "admin123"
            
            # Usamos uma query direta para evitar problemas de mapeamento no arranque
            from sqlalchemy import text
            res = sessao.execute(text("SELECT id_utilizador FROM utilizador WHERE username = :u"), {"u": admin_username}).first()
            
            if not res:
                logger.info("Administrador não encontrado. A criar...")
                # Primeiro verificar se o funcionário já existe para evitar erro de chave duplicada
                existe_func = sessao.get(FuncionarioHospital, 1)
                if not existe_func:
                    func_admin = FuncionarioHospital(num_func=1, sexo="M", tipo_func="ADMIN")
                    sessao.add(func_admin)
                    sessao.flush() # Garante que o funcionário existe antes de criar o utilizador
                
                papel_admin = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == "ADMIN")).first()
                
                if papel_admin:
                    novo_admin = Utilizador(
                        nome_utilizador=admin_username,
                        nome_completo="Administrador do Sistema",
                        email="admin@urgenciasg2.pt",
                        hash_palavra_passe=obter_hash_palavra_passe("admin123"),
                        id_role=papel_admin.id_role,
                        num_func=1,
                        ativo=True
                    )
                    sessao.add(novo_admin)
                else:
                    logger.error("ERRO: Papel ADMIN não encontrado na BD!")
                
            sessao.commit()
            logger.info("Inicialização da BD concluída com sucesso.")

    except Exception as e:
        logger.error(f"FALHA CRÍTICA NA INICIALIZAÇÃO DA BD: {str(e)}")
        # Re-raise para o Uvicorn saber que deve parar, mas agora temos o log
        raise e


def obter_sessao():
    """ 
    Função usada pelas rotas da API para obter uma ligação à BD.
    Garante que a ligação é fechada automaticamente no fim do pedido.
    """
    with Session(engine) as sessao:
        yield sessao
