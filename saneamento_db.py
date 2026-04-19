import psycopg2

def saneamento_total():
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/urgencias_g2")
    cur = conn.cursor()
    
    try:
        print("A aplicar saneamento total da base de dados...")
        
        # 1. Limpar tabelas de utilizadores para evitar conflitos de FK
        cur.execute("TRUNCATE TABLE audit_log CASCADE;")
        cur.execute("TRUNCATE TABLE utilizador CASCADE;")
        
        # 2. Garantir que a tabela ROLE está perfeita
        cur.execute("DELETE FROM role;")
        cur.execute("""
            INSERT INTO role (id_role, nome) VALUES 
            (1, 'ADMIN'), (2, 'MEDICO'), (3, 'ENFERMEIRO'), (4, 'RECECIONISTA');
        """)

        # 3. Adicionar as Chaves Estrangeiras (FKs) em falta na tabela utilizador
        print("A criar ligações de integridade (FKs)...")
        cur.execute("""
            ALTER TABLE utilizador 
            ADD CONSTRAINT fk_utilizador_role 
            FOREIGN KEY (id_role) REFERENCES role(id_role);
        """)
        cur.execute("""
            ALTER TABLE utilizador 
            ADD CONSTRAINT fk_utilizador_funcionario 
            FOREIGN KEY (num_func) REFERENCES funcionario_hospital(num_func) ON DELETE SET NULL;
        """)

        # 4. Criar Admin padrão
        import bcrypt
        salt = bcrypt.gensalt()
        pwd_hash = bcrypt.hashpw("Hospital#2026!".encode('utf-8'), salt).decode('utf-8')
        
        cur.execute("""
            INSERT INTO utilizador (username, nome_completo, email, password_hash, id_role, ativo)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, ("admin", "Administrador Principal", "admin@hospital.com", pwd_hash, 1, True))

        conn.commit()
        print("Saneamento concluído com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro no saneamento: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    saneamento_total()
