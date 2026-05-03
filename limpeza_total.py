from sqlmodel import create_engine, Session, text

engine = create_engine('postgresql://postgres:admin@localhost:5432/urgencias_g2')

def limpar_e_atualizar():
    with Session(engine) as session:
        print("1. A limpar tabelas de dados clínicos...")
        try:
            # CASCADE garante que todas as referências são limpas
            session.execute(text("TRUNCATE internamento, prescricao, \"Envolve\", ato, triagem, episodio_urgencia, email_validation, password_reset, audit_log CASCADE;"))
            
            print("2. A limpar utilizadores (mantendo admin)...")
            session.execute(text("DELETE FROM utilizador WHERE username != 'admin';"))
            
            print("3. A limpar utentes e hospitais...")
            session.execute(text("TRUNCATE utente, hospital CASCADE;"))

            print("4. A atualizar a estrutura da tabela Utente...")
            session.execute(text("ALTER TABLE utente ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;"))
            session.execute(text("ALTER TABLE utente ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);"))
            session.execute(text("ALTER TABLE utente ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT FALSE;"))
            session.execute(text("ALTER TABLE utente ADD COLUMN IF NOT EXISTS primeiro_acesso BOOLEAN DEFAULT TRUE;"))
            
            session.commit()
            print("\n✅ SUCESSO: Base de dados limpa e tabela Utente preparada.")
        except Exception as e:
            session.rollback()
            print(f"\n❌ ERRO: {str(e)}")

if __name__ == "__main__":
    limpar_e_atualizar()
