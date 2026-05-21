import psycopg2

def corrigir_suporte_profissionais():
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/urgencias_g2")
    cur = conn.cursor()
    
    try:
        print("A ajustar tamanhos de campos e tabelas...")
        # Alargar o campo sexo para aceitar nomes completos ou letras
        cur.execute("ALTER TABLE funcionario_hospital ALTER COLUMN sexo TYPE VARCHAR(20);")
        
        # Garantir que as tabelas específicas existem e estão ligadas corretamente
        cur.execute("""
            CREATE TABLE IF NOT EXISTS enfermeiro (
                num_func INTEGER PRIMARY KEY REFERENCES funcionario_hospital(num_func) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS medico (
                num_func INTEGER PRIMARY KEY REFERENCES funcionario_hospital(num_func) ON DELETE CASCADE,
                estagiario VARCHAR(50)
            );
        """)
        
        conn.commit()
        print("Correção aplicada com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao aplicar correção: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    corrigir_suporte_profissionais()
