import psycopg2

def corrigir_base_dados():
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/urgencias_g2")
    cur = conn.cursor()
    
    try:
        print("A sincronizar papéis (Roles)...")
        papeis = [
            (1, 'ADMIN'),
            (2, 'MEDICO'),
            (3, 'ENFERMEIRO'),
            (4, 'RECECIONISTA')
        ]
        for id_role, nome in papeis:
            cur.execute("""
                INSERT INTO role (id_role, nome) 
                VALUES (%s, %s) 
                ON CONFLICT (id_role) DO UPDATE SET nome = EXCLUDED.nome;
            """, (id_role, nome))
        
        print("A garantir que as tabelas de suporte existem...")
        # Caso tenham sido apagadas por acidente no CASCADE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS funcionario_hospital (
                num_func INTEGER PRIMARY KEY,
                sexo VARCHAR(1),
                tipo_func VARCHAR(20)
            );
            CREATE TABLE IF NOT EXISTS enfermeiro (
                num_func INTEGER PRIMARY KEY REFERENCES funcionario_hospital(num_func)
            );
            CREATE TABLE IF NOT EXISTS medico (
                num_func INTEGER PRIMARY KEY REFERENCES funcionario_hospital(num_func),
                estagiario VARCHAR(1)
            );
        """)
        
        conn.commit()
        print("Base de dados sincronizada com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao sincronizar: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    corrigir_base_dados()
