import pyotp
import qrcode
import io
import base64
import random
import re
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, text
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from ..core.db import obter_sessao
from ..core.security import verificar_palavra_passe, criar_token_acesso, obter_hash_palavra_passe, RoleChecker, obter_utilizador_atual
from ..models.models import Utilizador, PapelUtilizador, FuncionarioHospital, Medico, Enfermeiro, EmailValidation, PasswordReset
from ..core.audit import log_audit
from ..core.email import enviar_email_ativacao, enviar_email_recuperacao_username, enviar_email_recuperacao_password

router = APIRouter()
admin_only = RoleChecker(["ADMIN"])

# --- SCHEMAS ---
class LoginMFA(BaseModel):
    username: str
    mfa_code: str

class RecuperarConta(BaseModel):
    email: EmailStr

class RedefinirPassword(BaseModel):
    token: str
    nova_password: str

class CriarUtilizador(BaseModel):
    nome_utilizador: str
    nome_completo: str
    email: EmailStr
    palavra_passe: str
    id_role: Optional[int] = None # Uniformizado
    num_func: Optional[int] = None

    @staticmethod
    def validar_password(v: str) -> str:
        if len(v) < 12:
            raise ValueError('A password deve ter pelo menos 12 caracteres.')
        if not re.search(r"[A-Z]", v):
            raise ValueError('A password deve conter pelo menos uma letra maiúscula.')
        if not re.search(r"[0-9]", v):
            raise ValueError('A password deve conter pelo menos um número.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('A password deve conter pelo menos um caractere especial.')
        return v

class ValidarCodigo(BaseModel):
    email: EmailStr
    codigo: str

class AtualizarUtilizador(BaseModel):
    nome_completo: Optional[str] = None
    email: Optional[EmailStr] = None
    telemovel: Optional[str] = None
    palavra_passe: Optional[str] = None
    id_role: Optional[int] = None # Apenas Admin pode mudar
    ativo: Optional[bool] = None # Apenas Admin pode mudar

class LerUtilizador(BaseModel):
    id_utilizador: int
    nome_utilizador: str
    nome_completo: str
    email: str
    telemovel: Optional[str] = None
    id_role: int # Uniformizado - RESOLVE O ERRO DE VALIDAÇÃO
    num_func: Optional[int] = None
    ativo: bool

    class Config:
        from_attributes = True
        orm_mode = True # Compatibilidade com Pydantic v1 e v2

class CriarProfissional(BaseModel):
    num_func: int
    sexo: str
    tipo_func: str
    estagiario: Optional[str] = None

# --- AUTENTICAÇÃO ---
@router.post("/login")
def entrar(request: Request, dados_form: OAuth2PasswordRequestForm = Depends(), sessao: Session = Depends(obter_sessao)):
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == dados_form.username)).first()
    
    if not utilizador or not verificar_palavra_passe(dados_form.password, utilizador.hash_palavra_passe):
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
    
    if not utilizador.ativo:
        raise HTTPException(status_code=403, detail="Esta conta ainda não foi ativada.")
    
    if utilizador.mfa_ativo:
        return {"mfa_required": True, "mfa_setup_complete": True, "username": utilizador.nome_utilizador}
    else:
        papel = sessao.get(PapelUtilizador, utilizador.id_role)
        if papel and papel.nome == "ADMIN":
            token_acesso = criar_token_acesso(dados={"sub": utilizador.nome_utilizador, "role": papel.nome})
            return {"access_token": token_acesso, "token_type": "bearer", "role": papel.nome}
            
        if not utilizador.mfa_secret:
            utilizador.mfa_secret = pyotp.random_base32()
            sessao.add(utilizador)
            sessao.commit()
            
        totp_url = pyotp.totp.TOTP(utilizador.mfa_secret).provisioning_uri(name=utilizador.nome_utilizador, issuer_name="PortalClinico_G2")
        
        # Gerar QR Code localmente (Base64) em vez de usar API externa
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "mfa_required": True, 
            "mfa_setup_complete": False, 
            "username": utilizador.nome_utilizador, 
            "qr_code_url": totp_url, 
            "qr_code_image": f"data:image/png;base64,{qr_code_base64}",
            "secret": utilizador.mfa_secret
        }

@router.post("/login/mfa")
def verificar_mfa(request: Request, dados: LoginMFA, sessao: Session = Depends(obter_sessao)):
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.nome_utilizador == dados.username)).first()
    if not utilizador or not utilizador.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA não configurado")
    
    totp = pyotp.TOTP(utilizador.mfa_secret)
    if not totp.verify(dados.mfa_code):
        raise HTTPException(status_code=401, detail="Código MFA inválido")
    
    if not utilizador.mfa_ativo:
        utilizador.mfa_ativo = True
        sessao.add(utilizador)
        sessao.commit()

    papel = sessao.get(PapelUtilizador, utilizador.id_role)
    token_acesso = criar_token_acesso(dados={"sub": utilizador.nome_utilizador, "role": papel.nome})
    return {"access_token": token_acesso, "token_type": "bearer", "role": papel.nome}

@router.post("/activate")
def ativar_conta(dados: ValidarCodigo, sessao: Session = Depends(obter_sessao)):
    email_limpo = dados.email.lower().strip()
    validacao = sessao.exec(select(EmailValidation).where(
        EmailValidation.email == email_limpo,
        EmailValidation.codigo == dados.codigo,
        EmailValidation.utilizado == False,
        EmailValidation.expira_em > datetime.now()
    )).first()
    
    if not validacao:
        # Debug: Verificar se existe pelo menos o código para outro email ou algo assim
        existe_codigo = sessao.exec(select(EmailValidation).where(EmailValidation.codigo == dados.codigo)).first()
        if existe_codigo:
            print(f"DEBUG: Código {dados.codigo} encontrado mas para email {existe_codigo.email} (esperado {email_limpo})")
        raise HTTPException(status_code=400, detail="Código inválido ou expirado")
    
    validacao.utilizado = True
    sessao.add(validacao)

    # 1. Tentar ativar Utilizador (Staff)
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.email == email_limpo)).first()
    if utilizador:
        utilizador.ativo = True
        sessao.add(utilizador)
        sessao.commit()
        return {"message": "Conta de profissional ativada com sucesso!"}

    # 2. Tentar ativar Utente (Mobile)
    utente = sessao.exec(select(Utente).where(Utente.email == email_limpo)).first()
    if utente:
        utente.ativo = True
        sessao.add(utente)
        sessao.commit()
        return {"message": "Conta de utente ativada! Já pode aceder à App Mobile."}

    raise HTTPException(status_code=404, detail="Utilizador/Utente não encontrado para este e-mail.")
# --- RECUPERAÇÃO DE CONTA ---
@router.post("/forgot-username")
async def recuperar_utilizador(dados: RecuperarConta, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    email_limpo = dados.email.lower().strip()
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.email == email_limpo)).first()
    
    if utilizador:
        background_tasks.add_task(enviar_email_recuperacao_username, email_limpo, utilizador.nome_completo, utilizador.nome_utilizador)
    
    # Retornamos sempre sucesso por segurança (não enumerar utilizadores)
    return {"message": "Se o e-mail existir no nosso sistema, receberá os dados em breve."}

@router.post("/forgot-password")
async def recuperar_password(dados: RecuperarConta, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    email_limpo = dados.email.lower().strip()
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.email == email_limpo)).first()
    
    if utilizador:
        token = str(uuid.uuid4())
        reset = PasswordReset(
            email=email_limpo,
            token=token,
            expira_em=datetime.now() + timedelta(hours=1)
        )
        sessao.add(reset)
        sessao.commit()
        
        # URL do frontend (ajustar conforme necessário)
        link = f"http://localhost:3000/reset-password?token={token}"
        background_tasks.add_task(enviar_email_recuperacao_password, email_limpo, utilizador.nome_completo, link)
        
    return {"message": "Se o e-mail existir no nosso sistema, receberá um link de recuperação em breve."}

@router.post("/reset-password")
def confirmar_redefinicao_password(dados: RedefinirPassword, sessao: Session = Depends(obter_sessao)):
    # Reutilizamos a lógica de validação de password
    try:
        CriarUtilizador.validar_password(dados.nova_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    reset = sessao.exec(select(PasswordReset).where(
        PasswordReset.token == dados.token,
        PasswordReset.utilizado == False,
        PasswordReset.expira_em > datetime.now()
    )).first()
    
    if not reset:
        raise HTTPException(status_code=400, detail="Link inválido ou expirado.")
    
    utilizador = sessao.exec(select(Utilizador).where(Utilizador.email == reset.email)).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    
    utilizador.hash_palavra_passe = obter_hash_palavra_passe(dados.nova_password)
    reset.utilizado = True
    
    sessao.add(utilizador)
    sessao.add(reset)
    sessao.commit()
    
    return {"message": "Palavra-passe redefinida com sucesso!"}

# --- GESTÃO DE UTILIZADORES ---
from ..core.email import enviar_email_ativacao
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks

@router.post("/users", response_model=LerUtilizador, dependencies=[Depends(admin_only)])
def criar_utilizador(request: Request, utilizador_in: CriarUtilizador, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    try:
        CriarUtilizador.validar_password(utilizador_in.palavra_passe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    email_limpo = utilizador_in.email.lower().strip()
    
    # Determinar id_role automaticamente se tiver num_func
    id_role = utilizador_in.id_role
    if utilizador_in.num_func:
        func = sessao.get(FuncionarioHospital, utilizador_in.num_func)
        if not func:
            raise HTTPException(status_code=400, detail="Funcionário não encontrado.")
        
        papel = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == func.tipo_func)).first()
        if papel:
            id_role = papel.id_role

    if not id_role:
        raise HTTPException(status_code=400, detail="O cargo/função é obrigatório.")

    db_utilizador = Utilizador(
        nome_utilizador=utilizador_in.nome_utilizador,
        nome_completo=utilizador_in.nome_completo,
        email=email_limpo,
        hash_palavra_passe=obter_hash_palavra_passe(utilizador_in.palavra_passe),
        id_role=id_role,
        num_func=utilizador_in.num_func,
        ativo=False
    )
    
    try:
        sessao.add(db_utilizador)
        codigo = f"{random.randint(100000, 999999)}"
        validacao = EmailValidation(email=email_limpo, codigo=codigo, expira_em=datetime.now() + timedelta(hours=24))
        sessao.add(validacao)
        sessao.commit()
        
        # AGENDAR ENVIO DE EMAIL REAL EM BACKGROUND
        background_tasks.add_task(enviar_email_ativacao, email_limpo, utilizador_in.nome_completo, codigo)
        
        print(f"\n📧 [DEBUG] Código de ativação para {utilizador_in.email}: {codigo}\n")
        
        sessao.refresh(db_utilizador)
        return db_utilizador
    except Exception:
        sessao.rollback()
        raise HTTPException(status_code=400, detail="Username ou e-mail já existe.")

@router.get("/users/me", response_model=LerUtilizador)
def obter_perfil_atual(utilizador_atual: Utilizador = Depends(obter_utilizador_atual)):
    return utilizador_atual

@router.get("/users", response_model=List[LerUtilizador], dependencies=[Depends(admin_only)])
def listar_utilizadores(sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(Utilizador)).all()

@router.patch("/users/me", response_model=LerUtilizador)
def atualizar_proprio_perfil(dados: AtualizarUtilizador, utilizador_atual: Utilizador = Depends(obter_utilizador_atual), sessao: Session = Depends(obter_sessao)):
    # Impedir que o utilizador mude campos que só o Admin pode mudar
    if dados.id_role is not None or dados.ativo is not None:
        raise HTTPException(status_code=403, detail="Não tem permissão para alterar o seu cargo ou estado da conta.")
    
    # Atualizar campos permitidos
    if dados.nome_completo: utilizador_atual.nome_completo = dados.nome_completo
    if dados.email: utilizador_atual.email = dados.email.lower().strip()
    if dados.telemovel: utilizador_atual.telemovel = dados.telemovel
    if dados.palavra_passe:
        try:
            CriarUtilizador.validar_password(dados.palavra_passe)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        utilizador_atual.hash_palavra_passe = obter_hash_palavra_passe(dados.palavra_passe)

    sessao.add(utilizador_atual)
    sessao.commit()
    sessao.refresh(utilizador_atual)
    return utilizador_atual

@router.patch("/users/{id_utilizador}", response_model=LerUtilizador, dependencies=[Depends(admin_only)])
def atualizar_utilizador_admin(id_utilizador: int, dados: AtualizarUtilizador, sessao: Session = Depends(obter_sessao)):
    utilizador = sessao.get(Utilizador, id_utilizador)
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    # Admin pode editar campos adicionais
    if dados.nome_completo: utilizador.nome_completo = dados.nome_completo
    if dados.email: utilizador.email = dados.email.lower().strip()
    if dados.telemovel: utilizador.telemovel = dados.telemovel
    if dados.id_role: utilizador.id_role = dados.id_role
    if dados.ativo is not None: utilizador.ativo = dados.ativo
    if dados.palavra_passe:
        try:
            CriarUtilizador.validar_password(dados.palavra_passe)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        utilizador.hash_palavra_passe = obter_hash_palavra_passe(dados.palavra_passe)

    sessao.add(utilizador)
    sessao.commit()
    sessao.refresh(utilizador)
    return utilizador

@router.delete("/users/{id_utilizador}", dependencies=[Depends(admin_only)])
def eliminar_utilizador(id_utilizador: int, sessao: Session = Depends(obter_sessao)):
    utilizador = sessao.get(Utilizador, id_utilizador)
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    # Limpar dependências que impedem a remoção (Foreign Keys)
    sessao.execute(text("DELETE FROM audit_log WHERE id_utilizador = :uid"), {"uid": id_utilizador})
    sessao.execute(text("DELETE FROM email_validation WHERE email = :email"), {"email": utilizador.email})
    sessao.execute(text("DELETE FROM password_reset WHERE email = :email"), {"email": utilizador.email})

    sessao.delete(utilizador)
    try:
        sessao.commit()
        return {"message": f"Utilizador {utilizador.nome_utilizador} eliminado com sucesso"}
    except Exception as e:
        sessao.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao eliminar utilizador: {str(e)}")

@router.post("/professionals", dependencies=[Depends(admin_only)])
def criar_profissional(profissional: CriarProfissional, sessao: Session = Depends(obter_sessao)):
    # 1. Verificar se o funcionário já existe na tabela base
    existente = sessao.get(FuncionarioHospital, profissional.num_func)
    if existente:
        raise HTTPException(status_code=400, detail=f"O funcionário {profissional.num_func} já está registado.")

    try:
        # 2. Criar o registro na tabela base de funcionários
        db_func = FuncionarioHospital(
            num_func=profissional.num_func, 
            sexo=profissional.sexo, 
            tipo_func=profissional.tipo_func
        )
        sessao.add(db_func)
        
        # FORÇAR GRAVAÇÃO TEMPORÁRIA: Garante que o funcionário existe antes de criar o enfermeiro/médico
        sessao.flush() 
        
        # 3. Criar registro nas tabelas específicas
        if profissional.tipo_func == 'MEDICO':
            db_medico = Medico(num_func=profissional.num_func, estagiario=profissional.estagiario)
            sessao.add(db_medico)
        elif profissional.tipo_func == 'ENFERMEIRO':
            db_enfermeiro = Enfermeiro(num_func=profissional.num_func)
            sessao.add(db_enfermeiro)
        
        sessao.commit()
        print(f"SUCESSO: Profissional {profissional.num_func} ({profissional.tipo_func}) criado.")
        return {"message": "Profissional criado com sucesso"}
    except Exception as e:
        sessao.rollback()
        print(f"ERRO CRÍTICO AO CRIAR PROFISSIONAL: {str(e)}")
        # Se o erro for de duplicado na tabela específica mas não na base
        raise HTTPException(status_code=500, detail=f"Erro na base de dados: {str(e)}")

@router.get("/roles", response_model=List[PapelUtilizador])
def obter_papeis(sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(PapelUtilizador)).all()

@router.get("/professionals/{num_func}")
def obter_profissional(num_func: int, sessao: Session = Depends(obter_sessao)):
    funcionario = sessao.get(FuncionarioHospital, num_func)
    if not funcionario:
        raise HTTPException(status_code=404, detail="Não encontrado")
    papel = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == funcionario.tipo_func)).first()
    return {
        "num_func": funcionario.num_func,
        "tipo_func": funcionario.tipo_func,
        "id_role": papel.id_role if papel else None
    }
