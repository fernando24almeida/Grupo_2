import os
import sys
from pydantic_settings import BaseSettings

# Adicionar o diretório atual ao path para importar as configurações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import configuracoes

def debug_env():
    print("--- DEBUG AMBIENTE ---")
    print(f"Diretório de trabalho: {os.getcwd()}")
    print(f"DATABASE_URL (configuracoes): {configuracoes.DATABASE_URL.split('@')[-1]}")
    print(f"DATABASE_URL (os.environ): {os.environ.get('DATABASE_URL')}")
    
    # Verificar se existe algum .env escondido
    posseis_env = [".env", "backend/.env", "app/.env"]
    for f in posseis_env:
        if os.path.exists(f):
            print(f"Arquivo encontrado: {f}")
        else:
            print(f"Arquivo não encontrado: {f}")

if __name__ == "__main__":
    debug_env()
