import pyotp
import qrcode
import io
import base64
import random
import re
import uuid
import string
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, text
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from ..core.db import obter_sessao
from ..core.security import verificar_palavra_passe, criar_token_acesso, obter_hash_palavra_passe, RoleChecker, obter_utilizador_atual
from ..models.models import Utilizador, PapelUtilizador, FuncionarioHospital, Medico, Enfermeiro, EmailValidation, PasswordReset, AuditLog, Utente, EpisodioUrgencia, Triagem, Ato
from ..core.audit import log_audit
from ..core.email import enviar_email_ativacao, enviar_email_recuperacao_username, enviar_email_recuperacao_password

# =============================================================================
# ROTAS DE AUTENTICAÇÃO E GESTÃO DE UTILIZADORES
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro trata das 'portas de entrada'. Aqui definimos como as pessoas 
# fazem login, como ativam as contas e como o Administrador gere a equipa.
# Cada função aqui corresponde a um botão ou ação no ecrã de login/perfil.
# =============================================================================

router = APIRouter()
admin_only = RoleChecker(["ADMIN"])

# --- SCHEMAS (MOLDES DE DADOS) ---

class LoginMFA(BaseModel):
    username: str
    mfa_code: str

class LerUtilizador(BaseModel):
    id_utilizador: int
    nome_utilizador: str
    nome_completo: str
    email: str
    telemovel: Optional[str] = None
    id_role: int
    num_func: Optional[int] = None
    ativo: bool
    mfa_ativo: bool = False
    estagiario: Optional[str] = None
    especialidade: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CriarUtilizador(BaseModel):
    nome_utilizador: str
    nome_completo: str
    email: EmailStr
    palavra_passe: str
    id_role: Optional[int] = None
    num_func: Optional[int] = None

class ValidarCodigo(BaseModel):
    email: EmailStr
    codigo: str

class AtualizarUtilizador(BaseModel):
    nome_completo: Optional[str] = None
    email: Optional[EmailStr] = None
    telemovel: Optional[str] = None
    id_role: Optional[int] = None
    ativo: Optional[bool] = None
    palavra_passe: Optional[str] = None
    estagiario: Optional[str] = None
    especialidade: Optional[str] = None

class CriarProfissional(BaseModel):
    num_func: int
    sexo: str
    tipo_func: str
    estagiario: Optional[str] = None

# --- AUTENTICAÇÃO ---

@router.post("/login")
def entrar(request: Request, dados_form: OAuth2PasswordRequestForm = Depends(), sessao: Session = Depends(obter_sessao)):
    """ 
    Ação de Login. Verifica credenciais de Staff e Utentes.
    Inicia o fluxo de MFA para profissionais.
    """
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == dados_form.username)).first()
    
    if utilizador:
        if not verificar_palavra_passe(dados_form.password, utilizador.hash_palavra_passe):
            raise HTTPException(status_code=401, detail="Credenciais incorretas")
        
        if not utilizador.ativo:
            raise HTTPException(status_code=403, detail="Conta não ativada.")
        
        if utilizador.mfa_ativo:
            return {"mfa_required": True, "mfa_setup_complete": True, "username": utilizador.nome_utilizador}
        else:
            if not utilizador.mfa_secret:
                utilizador.mfa_secret = pyotp.random_base32()
                sessao.add(utilizador)
                sessao.commit()
            
            totp = pyotp.TOTP(utilizador.mfa_secret)
            uri = totp.provisioning_uri(name=utilizador.email, issuer_name="Urgências G2")
            img = qrcode.make(uri)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_str = base64.b64encode(buf.getvalue()).decode()
            
            return {
                "mfa_required": True,
                "mfa_setup_complete": False,
                "username": utilizador.nome_utilizador,
                "qr_code_image": f"data:image/png;base64,{img_str}",
                "secret": utilizador.mfa_secret
            }

    # Tentar Utente
    if dados_form.username.isdigit():
        utente = sessao.get(Utente, int(dados_form.username))
        if utente and verificar_palavra_passe(dados_form.password, utente.password_hash):
            token = criar_token_acesso(dados={"sub": str(utente.num_utente), "role": "UTENTE"})
            return {"access_token": token, "token_type": "bearer", "role": "UTENTE"}

    raise HTTPException(status_code=401, detail="Utilizador não encontrado")
class RecoverRequest(BaseModel):
    num_utente: str

# --- AUTENTICAÇÃO ---

@router.post("/login/mfa")
def verificar_mfa(dados: LoginMFA, sessao: Session = Depends(obter_sessao)):
    """ Completa o login do profissional com o código do telemóvel. """
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == dados.username)).first()
    if not utilizador or not utilizador.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA não configurado")

    totp = pyotp.TOTP(utilizador.mfa_secret)
    # Aumentamos a janela para 2 (60 seg antes/depois) para maior compatibilidade
    if not totp.verify(dados.mfa_code, valid_window=2):
        raise HTTPException(status_code=401, detail="Código inválido")

    if not utilizador.mfa_ativo:
        utilizador.mfa_ativo = True
        sessao.add(utilizador)
        sessao.commit()

    papel = sessao.get(PapelUtilizador, utilizador.id_role)
    token = criar_token_acesso(dados={"sub": utilizador.nome_utilizador, "role": papel.nome})
    return {"access_token": token, "token_type": "bearer", "role": papel.nome}

@router.post("/login/mfa/mobile")
def verificar_mfa_mobile(dados: LoginMFA, sessao: Session = Depends(obter_sessao)):
    """ Versão do MFA compatível com a App Mobile. """
    # Tentamos primeiro por username (Staff)
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == dados.username)).first()

    # Se não encontrar por username, tentamos por num_utente (Mobile/Utente)
    if not utilizador and dados.username.isdigit():
        utente = sessao.get(Utente, int(dados.username))
        if utente:
            # Utentes atualmente não têm MFA obrigatório neste fluxo, mas se o app pedir...
            token = criar_token_acesso(dados={"sub": str(utente.num_utente), "role": "UTENTE"})
            return {
                "success": True,
                "message": "MFA verificado",
                "data": {
                    "token": token,
                    "mfa_required": False,
                    "utente": {"num_utente": str(utente.num_utente), "nome": utente.nome}
                }
            }

    if not utilizador or not utilizador.mfa_secret:
        return {"success": False, "message": "Utilizador ou MFA inválido", "data": None}

    totp = pyotp.TOTP(utilizador.mfa_secret)
    if not totp.verify(dados.mfa_code, valid_window=2):
        return {"success": False, "message": "Código MFA incorreto", "data": None}

    papel = sessao.get(PapelUtilizador, utilizador.id_role)
    token = criar_token_acesso(dados={"sub": utilizador.nome_utilizador, "role": papel.nome})

    return {
        "success": True,
        "message": "Login concluído",
        "data": {
            "token": token,
            "mfa_required": False,
            "utente": {"nome_utilizador": utilizador.nome_utilizador, "nome": utilizador.nome_completo}
        }
    }

@router.post("/forgot-password")
def recuperar_acesso(dados: RecoverRequest, sessao: Session = Depends(obter_sessao)):
    """ Endpoint de simulação de recuperação de acesso para a App Mobile. """
    utente = sessao.get(Utente, int(dados.num_utente))
    if not utente:
        return {"success": False, "message": "Utente não encontrado", "data": None}

    # Em produção, enviaríamos um e-mail com link de reset.
    # Para este projeto, simulamos o envio.
    return {
        "success": True,
        "message": f"Instruções enviadas para o e-mail {utente.email}",
        "data": "OK"
    }

# --- GESTÃO DE UTILIZADORES ---

@router.get("/users/me", response_model=LerUtilizador)
def meu_perfil(utilizador_atual: Utilizador = Depends(obter_utilizador_atual)):
    """ Devolve os dados da pessoa que está logada agora. """
    return utilizador_atual

@router.patch("/users/me", response_model=LerUtilizador)
def atualizar_meu_perfil(dados: AtualizarUtilizador, sessao: Session = Depends(obter_sessao), utilizador_atual: Utilizador = Depends(obter_utilizador_atual)):
    """ Permite ao utilizador logado atualizar os seus próprios dados. """
    update_data = dados.dict(exclude_unset=True)
    
    if "palavra_passe" in update_data:
        pw = update_data.pop("palavra_passe")
        utilizador_atual.hash_palavra_passe = obter_hash_palavra_passe(pw)
    
    # Tratar campos de especialidade/estagiário se existirem e o utilizador for médico
    if utilizador_atual.num_func:
        medico = sessao.get(Medico, utilizador_atual.num_func)
        if medico:
            if "estagiario" in update_data:
                medico.estagiario = update_data.pop("estagiario")
            if "especialidade" in update_data:
                medico.especialidade = update_data.pop("especialidade")
            sessao.add(medico)

    for chave, valor in update_data.items():
        if hasattr(utilizador_atual, chave):
            setattr(utilizador_atual, chave, valor)
    
    sessao.add(utilizador_atual)
    sessao.commit()
    sessao.refresh(utilizador_atual)
    return utilizador_atual

@router.get("/users", response_model=List[LerUtilizador], dependencies=[Depends(admin_only)])
def listar_utilizadores(sessao: Session = Depends(obter_sessao)):
    """ Lista todos os profissionais para o Admin. """
    utilizadores = sessao.exec(select(Utilizador)).all()
    res = []
    for u in utilizadores:
        u_data = LerUtilizador.model_validate(u)
        if u.num_func:
            med = sessao.get(Medico, u.num_func)
            if med: u_data.especialidade = med.especialidade
        res.append(u_data)
    return res

@router.post("/users", response_model=LerUtilizador, dependencies=[Depends(admin_only)])
def criar_utilizador(utilizador_in: CriarUtilizador, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    """ Cria um novo utilizador e envia e-mail de ativação. """
    novo_user = Utilizador(
        nome_utilizador=utilizador_in.nome_utilizador,
        nome_completo=utilizador_in.nome_completo,
        email=utilizador_in.email,
        hash_palavra_passe=obter_hash_palavra_passe(utilizador_in.palavra_passe),
        id_role=utilizador_in.id_role,
        num_func=utilizador_in.num_func,
        ativo=False
    )
    sessao.add(novo_user)
    
    codigo = f"{random.randint(100000, 999999)}"
    validacao = EmailValidation(email=novo_user.email, codigo=codigo, expira_em=datetime.now(timezone.utc) + timedelta(hours=24))
    sessao.add(validacao)
    sessao.commit()
    
    background_tasks.add_task(enviar_email_ativacao, novo_user.email, novo_user.nome_completo, codigo)
    
    sessao.refresh(novo_user)
    return novo_user

@router.post("/users/{username}/reset-mfa", dependencies=[Depends(admin_only)])
def resetar_mfa(username: str, sessao: Session = Depends(obter_sessao)):
    """ O Admin pode limpar o MFA de um colega caso este perca o telemóvel. """
    user = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    user.mfa_ativo = False
    user.mfa_secret = None
    sessao.add(user)
    sessao.commit()
    return {"message": "MFA resetado. O utilizador terá de configurar um novo no próximo login."}

@router.patch("/users/{id_utilizador}", response_model=LerUtilizador, dependencies=[Depends(admin_only)])
def atualizar_utilizador(id_utilizador: int, dados: AtualizarUtilizador, sessao: Session = Depends(obter_sessao)):
    """ O Admin pode editar ou suspender contas. """
    user = sessao.get(Utilizador, id_utilizador)
    if not user:
        raise HTTPException(status_code=404, detail="Não encontrado")

    update_data = dados.dict(exclude_unset=True)
    for chave, valor in update_data.items():
        setattr(user, chave, valor)

    sessao.add(user)
    sessao.commit()
    sessao.refresh(user)
    return user

@router.delete("/users/{id_utilizador}", dependencies=[Depends(admin_only)])
def eliminar_utilizador(id_utilizador: int, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(obter_utilizador_atual)):
    """ Remove permanentemente um utilizador. """
    user = sessao.get(Utilizador, id_utilizador)
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    if user.id_utilizador == admin.id_utilizador:
        raise HTTPException(status_code=400, detail="Não pode eliminar a sua própria conta.")

    sessao.delete(user)
    sessao.commit()
    return {"message": "Utilizador eliminado com sucesso"}


@router.get("/roles", response_model=List[PapelUtilizador])
def listar_papeis(sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(PapelUtilizador)).all()

@router.get("/professionals/{num}", dependencies=[Depends(admin_only)])
def detetar_profissional(num: int, sessao: Session = Depends(obter_sessao)):
    """ Verifica se um funcionário existe e devolve o seu papel sugerido. """
    func = sessao.get(FuncionarioHospital, num)
    if not func:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    # Mapeamento de tipo para id_role
    mapping = {"MEDICO": 2, "ENFERMEIRO": 3, "RECECIONISTA": 4, "ADMIN": 1}
    return {"num_func": func.num_func, "tipo_func": func.tipo_func, "id_role": mapping.get(func.tipo_func)}

@router.post("/professionals", dependencies=[Depends(admin_only)])
def criar_profissional(dados: CriarProfissional, sessao: Session = Depends(obter_sessao)):
    """ Regista um novo profissional (Staff) no hospital. """
    existente = sessao.get(FuncionarioHospital, dados.num_func)
    if existente:
        raise HTTPException(status_code=400, detail="Número de funcionário já existe")
    
    novo_func = FuncionarioHospital(
        num_func=dados.num_func,
        sexo=dados.sexo,
        tipo_func=dados.tipo_func
    )
    sessao.add(novo_func)
    sessao.flush() # Garante que o funcionário existe antes de criar o registro especializado
    
    if dados.tipo_func == "MEDICO":
        novo_med = Medico(num_func=dados.num_func, estagiario=dados.estagiario)
        sessao.add(novo_med)
    elif dados.tipo_func == "ENFERMEIRO":
        novo_enf = Enfermeiro(num_func=dados.num_func)
        sessao.add(novo_enf)
        
    sessao.commit()
    return {"message": "Profissional registado com sucesso"}

@router.post("/users/{id_utilizador}/toggle-status", dependencies=[Depends(admin_only)])
def alternar_estado_utilizador(id_utilizador: int, sessao: Session = Depends(obter_sessao)):
    user = sessao.get(Utilizador, id_utilizador)
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    user.ativo = not user.ativo
    sessao.add(user)
    sessao.commit()
    return {"message": f"Estado alterado para {'Ativo' if user.ativo else 'Inativo'}"}

@router.post("/users/{id_utilizador}/resend-activation", dependencies=[Depends(admin_only)])
def reenviar_ativacao_utilizador(id_utilizador: int, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    user = sessao.get(Utilizador, id_utilizador)
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    codigo = f"{random.randint(100000, 999999)}"
    # Limpar validações antigas
    sessao.execute(text("DELETE FROM email_validation WHERE email = :e"), {"e": user.email})
    
    validacao = EmailValidation(email=user.email, codigo=codigo, expira_em=datetime.now(timezone.utc) + timedelta(hours=24))
    sessao.add(validacao)
    sessao.commit()
    
    background_tasks.add_task(enviar_email_ativacao, user.email, user.nome_completo, codigo)
    return {"message": "Novo código de ativação enviado por e-mail"}

@router.get("/audit", dependencies=[Depends(admin_only)])
def ver_audit(sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(AuditLog).order_by(AuditLog.data_hora.desc()).limit(100)).all()
