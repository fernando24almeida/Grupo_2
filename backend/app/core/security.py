from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from .config import configuracoes
from ..models.models import Utilizador, PapelUtilizador
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verificar_palavra_passe(palavra_passe_plana, hash_palavra_passe):
    try:
        return pwd_context.verify(palavra_passe_plana, hash_palavra_passe)
    except Exception as e:
        logger.error(f"Erro ao verificar palavra-passe: {e}")
        return False

def obter_hash_palavra_passe(palavra_passe):
    return pwd_context.hash(palavra_passe)

def criar_token_acesso(dados: dict, expira_delta: timedelta = None):
    para_codificar = dados.copy()
    agora = datetime.now(timezone.utc)
    if expira_delta:
        expira = agora + expira_delta
    else:
        expira = agora + timedelta(minutes=configuracoes.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Usar timestamp (int) para garantir compatibilidade com todas as bibliotecas JWT
    para_codificar.update({"exp": int(expira.timestamp())})
    
    jwt_codificado = jwt.encode(para_codificar, configuracoes.SECRET_KEY, algorithm=configuracoes.ALGORITHM)
    return jwt_codificado

def obter_utilizador_atual(token: str = Depends(oauth2_scheme)):
    # Importação local apenas do 'motor' para evitar erro circular com db.py
    from .db import motor

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
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token de acesso expirou",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning(f"Erro na validação do JWT: {e}")
        raise credentials_exception

    try:
        with Session(motor) as sessao:
            utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == username)).first()
            if not utilizador:
                # Opcional: Logar que o utilizador do token não existe na BD
                logger.warning(f"Utilizador '{username}' presente no token não encontrado na base de dados")
                raise credentials_exception
            
            # Detach do objeto para poder ser usado fora da sessão sem erros de Lazy Loading
            sessao.expunge(utilizador)
            return utilizador
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Erro de base de dados ao obter utilizador atual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao validar utilizador"
        )

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Utilizador = Depends(obter_utilizador_atual)):
        from .db import motor
        
        try:
            with Session(motor) as sessao:
                papel = sessao.get(PapelUtilizador, user.id_role)
                nome_papel = papel.nome if papel else "USER"
                
            if nome_papel not in self.allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Não tem permissão para aceder a este recurso"
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro no RoleChecker: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao verificar permissões de acesso"
            )
