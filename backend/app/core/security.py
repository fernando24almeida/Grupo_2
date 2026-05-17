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
    # Importação local para evitar erro circular
    from .db import motor
    from ..models.models import Utilizador, Utente
    from sqlmodel import Session, select

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Descodificar o token
        payload = jwt.decode(
            token, 
            configuracoes.SECRET_KEY, 
            algorithms=[configuracoes.ALGORITHM],
            options={"verify_aud": False}
        )
        username = payload.get("sub")
        
        if not username:
            raise credentials_exception
            
        print(f"DEBUG AUTH: Decoded username='{username}'")
        with Session(motor) as sessao:
            # 1. Tentar encontrar como Staff (Utilizador)
            query = select(Utilizador).where(Utilizador.nome_utilizador == str(username))
            staff = sessao.exec(query).first()
            print(f"DEBUG AUTH: Staff found? {staff is not None}")
            if staff:
                from ..models.models import PapelUtilizador
                papel = sessao.get(PapelUtilizador, staff.id_role)
                staff.role_name = papel.nome if papel else "USER"
                sessao.expunge(staff)
                return staff

            # 2. Tentar encontrar como Utente
            try:
                # Pode ser num_utente (int) ou o email (str)
                if str(username).isdigit():
                    user_id = int(username)
                    utente = sessao.get(Utente, user_id)
                else:
                    utente = sessao.exec(select(Utente).where(Utente.email == str(username))).first()

                if utente:
                    from ..models.models import PapelUtilizador
                    papel = sessao.get(PapelUtilizador, utente.id_role)
                    utente.role_name = papel.nome if papel else "UTENTE"
                    sessao.expunge(utente)
                    return utente
            except:
                pass

                
            raise credentials_exception

    except (JWTError, Exception) as e:
        print(f"DEBUG AUTH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise credentials_exception

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user = Depends(obter_utilizador_atual)):
        # COMPORTAMENTO ROBUSTO: Procurar papel na base de dados
        from ..models.models import PapelUtilizador
        from .db import motor
        
        with Session(motor) as sessao:
            papel = sessao.get(PapelUtilizador, user.id_role)
            nome_papel = papel.nome if papel else "USER"
            
        if nome_papel not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para aceder a este recurso"
            )
        return user
