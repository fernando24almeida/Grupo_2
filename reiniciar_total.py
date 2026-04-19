import psycopg2
import bcrypt
from datetime import datetime

def reiniciar_total():
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/urgencias_g2")
    cur = conn.cursor()
    
    try:
        print("A apagar tabelas existentes...")
        # Desativar restrições temporariamente para limpar tudo
        cur.execute("DROP TABLE IF EXISTS audit_log CASCADE;")
        cur.execute("DROP TABLE IF EXISTS email_validation CASCADE;")
        cur.execute("DROP TABLE IF EXISTS utilizador CASCADE;")
        # (Outras tabelas mantêm-se se necessário, mas vamos focar nos users)
        
        print("A recriar tabelas com nova estrutura...")
        cur.execute("""
            CREATE TABLE utilizador (
                id_utilizador SERIAL PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                nome_completo VARCHAR NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                password_hash VARCHAR NOT NULL,
                mfa_secret VARCHAR,
                mfa_ativo BOOLEAN DEFAULT FALSE,
                num_func INTEGER,
                id_role INTEGER,
                ativo BOOLEAN DEFAULT FALSE
            );
            
            CREATE TABLE email_validation (
                id SERIAL PRIMARY KEY,
                email VARCHAR NOT NULL,
                codigo VARCHAR NOT NULL,
                expira_em TIMESTAMP NOT NULL,
                utilizado BOOLEAN DEFAULT FALSE
            );
            
            CREATE TABLE audit_log (
                id SERIAL PRIMARY KEY,
                id_utilizador INTEGER,
                acao VARCHAR,
                recurso VARCHAR,
                id_recurso VARCHAR,
                detalhes TEXT,
                ip_origem VARCHAR,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Criar Admin inicial (sempre ativo para poder gerir o resto)
        print("A criar administrador mestre...")
        salt = bcrypt.gensalt()
        pwd_hash = bcrypt.hashpw("Hospital#2026!".encode('utf-8'), salt).decode('utf-8')
        
        cur.execute("""
            INSERT INTO utilizador (username, nome_completo, email, password_hash, id_role, ativo)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, ("admin", "Administrador do Sistema", "admin@hospital.com", pwd_hash, 1, True))
        
        conn.commit()
        print("Base de dados limpa e reiniciada com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro no reinício: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    reiniciar_total()
