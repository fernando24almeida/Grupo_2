from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
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
    agora = datetime.now(timezone.utc)
    if expira_delta:
        expira = agora + expira_delta
    else:
        expira = agora + timedelta(minutes=configuracoes.ACCESS_TOKEN_EXPIRE_MINUTES)
    para_codificar.update({"exp": expira})
    jwt_codificado = jwt.encode(para_codificar, configuracoes.SECRET_KEY, algorithm=configuracoes.ALGORITHM)
    return jwt_codificado

def obter_utilizador_atual(token: str = Depends(oauth2_scheme)):
    # Importação local para evitar erro circular
    from .db import motor
    from ..models.models import Utilizador

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, configuracoes.SECRET_KEY, algorithms=[configuracoes.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        with Session(motor) as sessao:
            utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == username)).first()
            if not utilizador:
                raise credentials_exception
            
            # Detach do objeto para poder ser usado fora da sessão
            sessao.expunge(utilizador)
            return utilizador
    except JWTError:
        raise credentials_exception

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: "Utilizador" = Depends(obter_utilizador_atual)):
        from .db import motor
        from ..models.models import PapelUtilizador
        
        with Session(motor) as sessao:
            papel = sessao.get(PapelUtilizador, user.id_role)
            nome_papel = papel.nome if papel else "USER"
            
        if nome_papel not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para aceder a este recurso"
            )
        return user
