from sqlmodel import Session
from ..models.models import AuditLog
from fastapi import Request
from typing import Optional

# =============================================================================
# MÓDULO DE AUDITORIA (REGISTO DE AÇÕES)
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro serve para escrever no 'livro de registos' do hospital. 
# Sempre que alguém faz algo importante (como mudar os dados de um utente), 
# chamamos esta função para guardar quem fez, o quê, quando e de onde (IP).
# =============================================================================

def log_audit(
    sessao: Session, 
    id_utilizador: Optional[int], 
    acao: str, 
    recurso: str, 
    id_recurso: Optional[str] = None, 
    detalhes: Optional[str] = None,
    request: Optional[Request] = None
):
    """
    Cria uma nova entrada na tabela audit_log.
    É como um 'post-it' de segurança que fica guardado para sempre.
    """
    ip = request.client.host if request and request.client else None
    
    log = AuditLog(
        id_utilizador=id_utilizador,
        acao=acao,
        recurso=recurso,
        id_recurso=id_recurso,
        detalhes=detalhes,
        ip_origem=ip
    )
    sessao.add(log)
    sessao.commit()
