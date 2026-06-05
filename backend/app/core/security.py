from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import List, Optional

from .config import configuracoes
from .db import obter_sessao
from ..models.models import Utilizador, PapelUtilizador

# =============================================================================
# MÓDULO DE SEGURANÇA (AUTENTICAÇÃO E ENCRIPTAÇÃO)
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro é o 'segurança' à porta do hospital. Ele trata de duas coisas:
# 1. Palavras-passe: Nunca as guardamos como texto (usamos um 'hash', que é uma 
#    impressão digital da password).
# 2. Tokens (JWT): Quando fazes login, recebes um 'passe' (token) que diz quem 
#    és e o que podes fazer, para não teres de pôr a pass em cada clique.
# =============================================================================

# Configuração para transformar passwords em 'impressões digitais' seguras
contexto_pass = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Onde a API vai buscar o token no navegador
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verificar_palavra_passe(palavra_passe_plana, palavra_passe_hash):
    """ Verifica se a pass que o utilizador escreveu bate certo com o hash na BD. """
    return contexto_pass.verify(palavra_passe_plana, palavra_passe_hash)

def obter_hash_palavra_passe(palavra_passe):
    """ Transforma uma password normal num código secreto (hash) para guardar na BD. """
    return contexto_pass.hash(palavra_passe)

def criar_token_acesso(dados: dict):
    """ 
    Cria o 'cartão de acesso' (JWT). 
    Guarda o nome do utilizador e quando é que o cartão expira.
    """
    dados_copia = dados.copy()
    expira = datetime.now(timezone.utc) + timedelta(minutes=configuracoes.ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_copia.update({"exp": expira})
    return jwt.encode(dados_copia, configuracoes.SECRET_KEY, algorithm=configuracoes.ALGORITHM)

async def obter_utilizador_atual(token: str = Depends(oauth2_scheme), sessao: Session = Depends(obter_sessao)):
    """
    Esta função corre em quase todas as rotas. Ela lê o token do utilizador, 
    verifica se é válido e vai à base de dados buscar quem ele é.
    """
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, configuracoes.SECRET_KEY, algorithms=[configuracoes.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise erro_credenciais
    except JWTError:
        raise erro_credenciais
        
    # Procurar o utilizador (Staff) pelo username
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == username)).first()
    
    # Se não for Staff, procurar por num_utente (Mobile)
    if not utilizador:
        from ..models.models import Utente
        if username.isdigit():
            utilizador = sessao.get(Utente, int(username))
            
    if utilizador is None:
        raise erro_credenciais
        
    # Adicionar o nome do papel (ADMIN, MEDICO...) para facilitar verificações
    papel = sessao.get(PapelUtilizador, utilizador.id_role)
    utilizador.role_name = papel.nome if papel else "USER"
    
    return utilizador

class RoleChecker:
    """
    Um 'filtro' que só deixa passar certas pessoas.
    Exemplo: @router.get(..., dependencies=[Depends(RoleChecker(["ADMIN"]))])
    """
    def __init__(self, papeis_permitidos: List[str]):
        self.papeis_permitidos = papeis_permitidos

    def __call__(self, utilizador: Utilizador = Depends(obter_utilizador_atual)):
        if utilizador.role_name not in self.papeis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Não tem permissões suficientes para realizar esta ação."
            )
        return utilizador
