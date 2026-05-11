from sqlalchemy import text
from sqlmodel import create_engine
import sys
import os

# Adicionar o diretório atual ao path para importar as configurações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import configuracoes

def migrar():
    print(f"--- Iniciando Migração da Base de Dados ---")
    motor = create_engine(configuracoes.DATABASE_URL)
    
    colunas_a_adicionar = [
        ("utente", "parentesco", "VARCHAR(100)"),
        ("episodio_urgencia", "id_utilizador_rececao", "INT REFERENCES utilizador(id_utilizador)"),
        ("ato", "diagnostico", "TEXT"),
        ("ato", "notas_clinicas", "TEXT"),
        ("ato", "exame_fisico", "TEXT"),
        ("ato", "decisao_clinica", "VARCHAR(50)"),
        ("internamento", "num_func_medico", "INT REFERENCES medico(num_func)")
    ]

    with motor.connect() as conexao:
        for tabela, coluna, tipo in colunas_a_adicionar:
            try:
                # Verificar se a coluna já existe para evitar erro
                check_sql = text(f"""
                    SELECT count(*) 
                    FROM information_schema.columns 
                    WHERE table_name='{tabela}' AND column_name='{coluna}';
                """)
                exists = conexao.execute(check_sql).scalar()
                
                if exists == 0:
                    print(f"Adicionando coluna '{coluna}' à tabela '{tabela}'...")
                    alter_sql = text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo};")
                    conexao.execute(alter_sql)
                    conexao.commit()
                    print(f"[OK] Coluna '{coluna}' adicionada.")
                else:
                    print(f"[SKIP] Coluna '{coluna}' já existe na tabela '{tabela}'.")
            except Exception as e:
                print(f"[ERRO] Falha ao processar {tabela}.{coluna}: {e}")
        
        # Remover a restrição de unicidade do email se existir
        try:
            print("Verificando restrição de unicidade do email no utente...")
            # Esta query tenta encontrar o nome da constraint de unique para o email
            find_constraint = text("""
                SELECT constraint_name 
                FROM information_schema.constraint_column_usage 
                WHERE table_name = 'utente' AND column_name = 'email'
                AND constraint_name LIKE '%key%';
            """)
            constraints = conexao.execute(find_constraint).fetchall()
            for row in constraints:
                c_name = row[0]
                print(f"Removendo restrição '{c_name}'...")
                conexao.execute(text(f"ALTER TABLE utente DROP CONSTRAINT {c_name};"))
                conexao.commit()
                print(f"[OK] Restrição '{c_name}' removida.")
        except Exception as e:
            print(f"[INFO] Nenhuma restrição de e-mail encontrada ou erro ao remover: {e}")

    print("--- Migração Concluída ---")

if __name__ == "__main__":
    migrar()
