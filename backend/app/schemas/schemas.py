from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class UtilizadorBase(BaseModel):
    nome_utilizador: str
    email: EmailStr

class UtilizadorCriar(UtilizadorBase):
    palavra_passe: str = Field(..., min_length=12)
    id_papel: int
    num_func: int | None = None

    @field_validator('palavra_passe')
    @classmethod
    def validar_complexidade_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError('A password deve conter pelo menos uma letra maiúscula.')
        if not re.search(r"[a-z]", v):
            raise ValueError('A password deve conter pelo menos uma letra minúscula.')
        if not re.search(r"[0-9]", v):
            raise ValueError('A password deve conter pelo menos um número.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('A password deve conter pelo menos um caractere especial.')
        return v

class UtilizadorLogin(BaseModel):
    nome_utilizador: str
    palavra_passe: str

class Token(BaseModel):
    access_token: str
    token_type: str
