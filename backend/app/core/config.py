import os
from pydantic_settings import BaseSettings

# =============================================================================
# CONFIGURAÇÕES GERAIS DO SISTEMA
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro guarda os "segredos" e definições do sistema, como o URL 
# da base de dados, chaves de segurança e definições de e-mail. Usamos 
# variáveis de ambiente para que estes dados sensíveis não fiquem expostos.
# =============================================================================

class Configuracoes(BaseSettings):
<<<<<<< HEAD
    """
    Esta classe lê os dados do ficheiro .env ou do ambiente (Docker).
    Se não encontrar nada, usa os valores padrão (default).
    """
    
    # Base de Dados (Onde guardamos tudo)
    # Se estivermos a correr localmente (Windows), usamos localhost.
    # Se estivermos no Docker, o Docker define o DATABASE_URL para "db".
    DATABASE_URL: str = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
    
    # Segurança (Chaves para trancar a porta e cifrar dados)
=======
    # O default é localhost para desenvolvimento, mas em produção (Render) deve vir do env
    DATABASE_URL: str = "postgresql://postgres:123456@127.0.0.1:5432/urgencias_g2"
>>>>>>> 755ba7b546f82761405dac367cee876e346ab523
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480 # O login dura 8 horas
    
    # Chave para Criptografia de Dados de Pacientes (AES)
    ENCRYPTION_KEY: str = "T0ZfU2VjcmV0X0VuY3J5cHRpb25fS2V5X0Zvcl9QYXRpZW50X0RhdGE="

    # Configurações de E-mail (Para enviar códigos de ativação)
    MAIL_USERNAME: str = "geral@sci.pt"
    MAIL_PASSWORD: str = "jbfn alir tral urks" # Password de aplicação
    MAIL_FROM: str = "geral@sci.pt"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Portal Clínico G2"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True

    model_config = {
        "env_file": ".env", # Tenta ler deste ficheiro se ele existir
        "case_sensitive": True
    }

# Criamos uma instância única para usar em todo o projeto
configuracoes = Configuracoes()
