from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from .config import configuracoes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verificar_palavra_passe(palavra_passe_plana, hash_palavra_passe):
    return pwd_context.verify(palavra_passe_plana, hash_palavra_passe)

def obter_hash_palavra_passe(palavra_passe):
    return pwd_context.hash(palavra_passe)

def criar_token_acesso(dados: dict, expira_delta: timedelta = None):
    para_codificar = dados.copy()
    if expira_delta:
        expira = datetime.utcnow() + expira_delta
    else:
        expira = datetime.utcnow() + timedelta(minutes=configuracoes.ACCESS_TOKEN_EXPIRE_MINUTES)
    para_codificar.update({"exp": expira})
    jwt_codificado = jwt.encode(para_codificar, configuracoes.SECRET_KEY, algorithm=configuracoes.ALGORITHM)
    return jwt_codificado

def obter_utilizador_atual(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, configuracoes.SECRET_KEY, algorithms=[configuracoes.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        return {"username": username, "role": role}
    except JWTError:
        raise credentials_exception

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user = Depends(obter_utilizador_atual)):
        if user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para aceder a este recurso"
            )
        return user
