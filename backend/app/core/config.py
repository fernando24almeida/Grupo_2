import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional

class Configuracoes(BaseSettings):
    # O default é localhost para desenvolvimento, mas em produção (Render) deve vir do env
    DATABASE_URL: str = "postgresql://postgres:admin@localhost:5432/urgencias_g2"
    
    SECRET_KEY: str = "supersecretkey"
    ENCRYPTION_KEY: str = "z2AkT7uJkt85JNw4pjZ5ZlblXpMjMQZ49QBT673bUEE=" # Deve ser gerada via Fernet.generate_key()
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Configurações SMTP (E-mail)
    MAIL_USERNAME: str = "geral@sci.pt"
    MAIL_PASSWORD: str = "jbfn alir tral urks"
    MAIL_FROM: str = "geral@sci.pt"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Portal Clínico G2"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True

    # Detectar se estamos no Render
    RENDER: bool = os.environ.get("RENDER", "false").lower() == "true"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_scheme(cls, v: str) -> str:
        if not v:
            return v
        # Render fornece URLs que começam com postgres://, mas o SQLAlchemy 1.4+ exige postgresql://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        
        # Se estivermos no Render e a URL ainda for localhost, há algo errado na configuração
        if os.environ.get("RENDER", "false").lower() == "true" and "localhost" in v:
            print("⚠️ AVISO: Detectado ambiente Render mas DATABASE_URL aponta para localhost!")
            
        return v

configuracoes = Configuracoes()
