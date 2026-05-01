from pydantic_settings import BaseSettings
from typing import Optional

class Configuracoes(BaseSettings):
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

    class Config:
        env_file = ".env"

configuracoes = Configuracoes()
