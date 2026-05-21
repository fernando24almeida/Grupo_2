import psycopg2
import bcrypt

def reiniciar_utilizadores():
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/urgencias_g2")
    cur = conn.cursor()
    
    try:
        print("A limpar tabela 'utilizador' e 'audit_log'...")
        cur.execute("TRUNCATE TABLE audit_log RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE utilizador RESTART IDENTITY CASCADE;")
        
        username = "admin"
        email = "admin@hospital.com"
        password_plana = "Hospital#2026!"
        
        # Gerar hash com bcrypt puro (sem passlib para evitar erros de versão)
        print(f"A gerar hash para {username}...")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_plana.encode('utf-8'), salt).decode('utf-8')
        
        id_role_admin = 1
        
        print(f"A inserir administrador na base de dados...")
        cur.execute("""
            INSERT INTO utilizador (username, email, password_hash, id_role, mfa_ativo, ativo)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (username, email, password_hash, id_role_admin, False, True))
        
        conn.commit()
        print("="*40)
        print("UTILIZADORES REINICIADOS COM SUCESSO")
        print(f"Utilizador: {username}")
        print(f"Password: {password_plana}")
        print(f"E-mail: {email}")
        print("="*40)
    except Exception as e:
        conn.rollback()
        print(f"Erro ao reiniciar: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    reiniciar_utilizadores()
