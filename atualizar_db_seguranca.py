import psycopg2

def atualizar_db():
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/urgencias_g2")
    cur = conn.cursor()
    
    try:
        print("A adicionar colunas à tabela 'utilizador'...")
        # Adicionar colunas se não existirem
        cur.execute("ALTER TABLE utilizador ADD COLUMN IF NOT EXISTS email VARCHAR;")
        cur.execute("ALTER TABLE utilizador ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR;")
        cur.execute("ALTER TABLE utilizador ADD COLUMN IF NOT EXISTS mfa_ativo BOOLEAN DEFAULT FALSE;")
        
        # Garantir que o admin tem um email para evitar erros (opcional)
        cur.execute("UPDATE utilizador SET email = 'admin@hospital.com' WHERE username = 'admin' AND email IS NULL;")
        
        print("A criar tabela 'audit_log'...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                id_utilizador INTEGER REFERENCES utilizador(id_utilizador),
                acao VARCHAR,
                recurso VARCHAR,
                id_recurso VARCHAR,
                detalhes TEXT,
                ip_origem VARCHAR,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("Base de dados atualizada com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    atualizar_db()
