from fastapi import Request
from sqlmodel import Session
from ..models.models import AuditLog
from datetime import datetime

def log_audit(db: Session, id_utilizador: int, acao: str, recurso: str, id_recurso: str = None, detalhes: str = None, request: Request = None):
    ip = request.client.host if request else "unknown"
    
    novo_log = AuditLog(
        id_utilizador=id_utilizador,
        acao=acao,
        recurso=recurso,
        id_recurso=id_recurso,
        detalhes=detalhes,
        ip_origem=ip,
        data_hora=datetime.now()
    )
    db.add(novo_log)
    db.commit()
