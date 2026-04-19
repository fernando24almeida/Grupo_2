import psycopg2

def auditoria_db():
    conn = psycopg2.connect("postgresql://postgres:admin@localhost:5432/urgencias_g2")
    cur = conn.cursor()
    
    try:
        print("\n--- TABELAS E COLUNAS ---")
        cur.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position;
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"Tabela: {row[0]:<20} | Coluna: {row[1]:<20} | Tipo: {row[2]:<15} | Null: {row[3]}")

        print("\n--- CHAVES ESTRANGEIRAS (RELAÇÕES) ---")
        cur.execute("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY';
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"{row[0]}.{row[1]} -> {row[2]}.{row[3]}")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    auditoria_db()
