from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

alter_queries = [
    "ALTER TABLE utilizador ADD COLUMN IF NOT EXISTS nome_completo VARCHAR(255) DEFAULT 'Administrador';",
    "ALTER TABLE utilizador ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;",
    "ALTER TABLE utilizador ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(255);",
    "ALTER TABLE utilizador ADD COLUMN IF NOT EXISTS mfa_ativo BOOLEAN DEFAULT FALSE;",
    "UPDATE utilizador SET email = 'admin@hospital.pt' WHERE username = 'admin' AND email IS NULL;",
    "ALTER TABLE utilizador ALTER COLUMN email SET NOT NULL;"
]

try:
    with engine.connect() as connection:
        for query in alter_queries:
            print(f"A executar: {query}")
            connection.execute(text(query))
            connection.commit()
    print("Banco de dados atualizado com sucesso!")
except Exception as e:
    print(f"Erro ao atualizar o banco de dados: {e}")
