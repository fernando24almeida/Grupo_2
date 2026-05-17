from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlmodel import Session, select, func, union_all
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, date
import random
import string

from ..core.db import obter_sessao
from ..models.models import (
    Utente, EpisodioUrgencia, Triagem, Ato, Prescricao, Internamento, 
    Hospital, Envolve, FuncionarioHospital, ServicoHospitalar, Utilizador, EmailValidation, AuditLog, PapelUtilizador
)
from ..core.security import (
    RoleChecker, obter_utilizador_atual, obter_hash_palavra_passe, 
    verificar_palavra_passe, criar_token_acesso
)
from ..core.audit import log_audit
from ..core.email import enviar_email_ativacao

router = APIRouter()
admin_only = RoleChecker(["ADMIN"])

# SCHEMAS
class CriarEpisodio(BaseModel):
    id_utente: int
    id_hospital: str
    data_h_entrada: Optional[datetime] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None
    id_utilizador_rececao: Optional[int] = None

class CriarTriagem(BaseModel):
    cod_epis: str
    tensao_arterial: str
    temperatura: float
    sintomas: str
    observacoes: Optional[str] = None
    num_func_enfermeiro: int

class AtualizarUtente(BaseModel):
    nome: Optional[str] = None
    telemovel: Optional[str] = None
    morada: Optional[str] = None
    sexo: Optional[str] = None
    localidade: Optional[str] = None
    data_nascimento: Optional[datetime] = None
    ativo: Optional[bool] = None
    password: Optional[str] = None

class AtualizarHospital(BaseModel):
    local_hosp: Optional[str] = None

class AtualizarEpisodio(BaseModel):
    data_h_entrada: Optional[datetime] = None
    data_h_saida: Optional[datetime] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None

class AtualizarEpisodioAuditado(AtualizarEpisodio):
    justificativa: str
    autorizacao: str

class AtualizarTriagemAuditada(BaseModel):
    prioridade: Optional[str] = None
    tensao_arterial: Optional[str] = None
    temperatura: Optional[float] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None
    justificativa: str
    autorizacao: str

class AtualizarAtoAuditado(BaseModel):
    tipo: Optional[str] = None
    data_h_fim: Optional[datetime] = None
    justificativa: str
    autorizacao: str

@router.patch("/episodes/{cod_epis}/audit", response_model=EpisodioUrgencia, dependencies=[Depends(admin_only)])
def atualizar_episodio_auditado(
    cod_epis: str, 
    dados: AtualizarEpisodioAuditado, 
    request: Request,
    sessao: Session = Depends(obter_sessao),
    admin: Utilizador = Depends(obter_utilizador_atual)
):
    db_episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not db_episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    
    # Registar Auditoria
    detalhes = f"Justificativa: {dados.justificativa} | Autorização: {dados.autorizacao}"
    log_audit(sessao, admin.id_utilizador, "UPDATE_AUDITED", "episodio_urgencia", cod_epis, detalhes, request)
    
    update_data = dados.dict(exclude_unset=True)
    del update_data["justificativa"]
    del update_data["autorizacao"]
    
    for chave, valor in update_data.items():
        setattr(db_episodio, chave, valor)
    
    sessao.add(db_episodio)
    sessao.commit()
    sessao.refresh(db_episodio)
    return db_episodio

@router.get("/triagens", response_model=List[Triagem], dependencies=[Depends(admin_only)])
def listar_triagens(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    if id_hospital:
        query = select(Triagem).join(EpisodioUrgencia, Triagem.cod_epis == EpisodioUrgencia.cod_epis).where(EpisodioUrgencia.id_hospital == id_hospital)
        return sessao.exec(query).all()
    return sessao.exec(select(Triagem)).all()

@router.patch("/triagens/{num_triagem}/audit", response_model=Triagem, dependencies=[Depends(admin_only)])
def atualizar_triagem_auditada(
    num_triagem: int, 
    dados: AtualizarTriagemAuditada, 
    request: Request,
    sessao: Session = Depends(obter_sessao),
    admin: Utilizador = Depends(obter_utilizador_atual)
):
    db_triagem = sessao.get(Triagem, num_triagem)
    if not db_triagem:
        raise HTTPException(status_code=404, detail="Triagem não encontrada")
    
    detalhes = f"Justificativa: {dados.justificativa} | Autorização: {dados.autorizacao}"
    log_audit(sessao, admin.id_utilizador, "UPDATE_AUDITED", "triagem", str(num_triagem), detalhes, request)
    
    update_data = dados.dict(exclude_unset=True)
    del update_data["justificativa"]
    del update_data["autorizacao"]
    
    for chave, valor in update_data.items():
        setattr(db_triagem, chave, valor)
    
    sessao.add(db_triagem)
    sessao.commit()
    sessao.refresh(db_triagem)
    return db_triagem

@router.get("/atos", response_model=List[Ato], dependencies=[Depends(admin_only)])
def listar_atos(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    if id_hospital:
        return sessao.exec(select(Ato).where(Ato.id_hosp == id_hospital)).all()
    return sessao.exec(select(Ato)).all()

@router.patch("/atos/{data_h_inicio}/audit", response_model=Ato, dependencies=[Depends(admin_only)])
def atualizar_ato_auditado(
    data_h_inicio: datetime, 
    dados: AtualizarAtoAuditado, 
    request: Request,
    sessao: Session = Depends(obter_sessao),
    admin: Utilizador = Depends(obter_utilizador_atual)
):
    db_ato = sessao.get(Ato, data_h_inicio)
    if not db_ato:
        raise HTTPException(status_code=404, detail="Ato clínico não encontrado")
    
    detalhes = f"Justificativa: {dados.justificativa} | Autorização: {dados.autorizacao}"
    log_audit(sessao, admin.id_utilizador, "UPDATE_AUDITED", "ato", str(data_h_inicio), detalhes, request)
    
    update_data = dados.dict(exclude_unset=True)
    del update_data["justificativa"]
    del update_data["autorizacao"]
    
    for chave, valor in update_data.items():
        setattr(db_ato, chave, valor)
    
    sessao.add(db_ato)
    sessao.commit()
    sessao.refresh(db_ato)
    return db_ato

# HOSPITAIS
@router.get("/hospitals", response_model=List[Hospital])
def ler_hospitais(sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(Hospital)).all()

@router.post("/hospitals", response_model=Hospital)
def criar_hospital(hospital: Hospital, sessao: Session = Depends(obter_sessao)):
    # Verificar se o hospital já existe pelo nome (Primary Key)
    db_hospital = sessao.get(Hospital, hospital.nome_hosp)
    if db_hospital:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"O hospital '{hospital.nome_hosp}' já está registado no sistema."
        )
    
    sessao.add(hospital)
    sessao.commit()
    sessao.refresh(hospital)
    return hospital

@router.patch("/hospitals/{nome_hosp}", response_model=Hospital, dependencies=[Depends(admin_only)])
def atualizar_hospital(nome_hosp: str, hospital_in: AtualizarHospital, sessao: Session = Depends(obter_sessao)):
    db_hospital = sessao.get(Hospital, nome_hosp)
    if not db_hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    dados = hospital_in.dict(exclude_unset=True)
    for chave, valor in dados.items():
        setattr(db_hospital, chave, valor)
    sessao.add(db_hospital)
    sessao.commit()
    sessao.refresh(db_hospital)
    return db_hospital

@router.delete("/hospitals/{nome_hosp}", dependencies=[Depends(admin_only)])
def eliminar_hospital(nome_hosp: str, sessao: Session = Depends(obter_sessao)):
    db_hospital = sessao.get(Hospital, nome_hosp)
    if not db_hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    sessao.delete(db_hospital)
    sessao.commit()
    return {"message": "Hospital eliminado com sucesso"}

# UTENTE
@router.get("/utentes/search", response_model=List[Utente])
def pesquisar_utente(
    num_utente: Optional[int] = None, 
    telemovel: Optional[str] = None, 
    sessao: Session = Depends(obter_sessao)
):
    query = select(Utente)
    if num_utente:
        query = query.where(Utente.num_utente == num_utente)
    elif telemovel:
        query = query.where(Utente.telemovel == telemovel)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Deve fornecer um número de utente ou um número de telemóvel para a pesquisa."
        )
    
    resultados = sessao.exec(query).all()
    return resultados

# SCHEMAS ADICIONAIS
class UtenteCreate(BaseModel):
    num_utente: int
    nome: str
    email: str
    telemovel: Optional[str] = None
    morada: Optional[str] = None
    localidade: Optional[str] = None
    sexo: Optional[str] = "M"
    data_nascimento: Optional[str] = None # Aceita string do frontend (YYYY-MM-DD)
    parentesco: Optional[str] = None

class LoginUtente(BaseModel):
    num_utente: int
    pin: str

class AlterarPinUtente(BaseModel):
    num_utente: int
    pin_atual: str
    novo_pin: str

@router.post("/utentes", response_model=Utente)
def criar_utente(dados: UtenteCreate, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    # 1. Verificar se o utente já existe pelo número
    existente_num = sessao.get(Utente, dados.num_utente)
    if existente_num:
        raise HTTPException(status_code=400, detail=f"O número de utente {dados.num_utente} já está registado.")
    
    # 2. Verificar se o e-mail já existe
    email_limpo = dados.email.lower().strip()
    existente_email = sessao.exec(select(Utente).where(Utente.email == email_limpo)).first()
    
    if existente_email and not dados.parentesco:
        raise HTTPException(
            status_code=400, 
            detail=f"O e-mail {dados.email} já está associado a outro utente ({existente_email.nome}). Para registar um novo utente com o mesmo e-mail, deve indicar o grau de parentesco (ex: Filho/a, Cônjuge)."
        )

    # 3. Tratar data de nascimento (converter string vazia para None)
    data_nasc = None
    if dados.data_nascimento and dados.data_nascimento.strip():
        try:
            if isinstance(dados.data_nascimento, str):
                data_nasc = datetime.strptime(dados.data_nascimento, "%Y-%m-%d").date()
            else:
                data_nasc = dados.data_nascimento
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data de nascimento inválido. Use AAAA-MM-DD.")
    
    # 4. Obter papel UTENTE
    papel_utente = sessao.exec(select(PapelUtilizador).where(PapelUtilizador.nome == "UTENTE")).first()
    if not papel_utente:
        # Fallback caso não exista (não deve acontecer após inicializar_bd)
        papel_utente = PapelUtilizador(nome="UTENTE")
        sessao.add(papel_utente)
        sessao.commit()
        sessao.refresh(papel_utente)

    # 5. Gerar PIN temporário
    pin_temporario = ''.join(random.choices(string.digits, k=6))
    
    # 6. Criar objeto Utente
    novo_utente = Utente(
        num_utente=dados.num_utente,
        nome=dados.nome,
        email=email_limpo,
        telemovel=dados.telemovel or None,
        morada=dados.morada or None,
        localidade=dados.localidade or None,
        sexo=dados.sexo or "M",
        data_nascimento=data_nasc,
        password_hash=obter_hash_palavra_passe(pin_temporario),
        ativo=False,
        primeiro_acesso=True,
        parentesco=dados.parentesco,
        id_role=papel_utente.id_role
    )
    
    # 7. Gerar código de ativação
    codigo_ativacao = f"{random.randint(100000, 999999)}"
    
    try:
        sessao.add(novo_utente)
        validacao = EmailValidation(
            email=novo_utente.email, 
            codigo=codigo_ativacao, 
            expira_em=datetime.now() + timedelta(hours=24)
        )
        sessao.add(validacao)
        sessao.commit()
        
        # 7. Enviar e-mail
        background_tasks.add_task(enviar_email_ativacao, novo_utente.email, novo_utente.nome, f"{codigo_ativacao} (PIN Mobile: {pin_temporario})")
        
        print(f"\n📧 [DEBUG MOBILE] Utente {novo_utente.num_utente} | PIN: {pin_temporario} | Código: {codigo_ativacao}\n")
        
        sessao.refresh(novo_utente)
        return novo_utente
    except Exception as e:
        sessao.rollback()
        print(f"ERRO CRÍTICO AO CRIAR UTENTE: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno na base de dados: {str(e)}")

@router.post("/utentes/login")
def login_utente(dados: LoginUtente, sessao: Session = Depends(obter_sessao)):
    utente = sessao.get(Utente, dados.num_utente)
    if not utente or not verificar_palavra_passe(dados.pin, utente.password_hash):
        raise HTTPException(status_code=401, detail="Número de utente ou PIN incorretos")

    if not utente.ativo:
        raise HTTPException(status_code=403, detail="Conta não ativada. Verifique o seu e-mail.")

    token = criar_token_acesso(dados={"sub": str(utente.num_utente), "role": "UTENTE"})

    return {
        "success": True,
        "message": "Login realizado com sucesso",
        "data": {
            "token": token,
            "mfa_required": False,
            "utente": {
                "num_utente": str(utente.num_utente),
                "nome": utente.nome,
                "email": utente.email
            }
        }
    }

@router.post("/utentes/change-pin")
def alterar_pin_utente(dados: AlterarPinUtente, sessao: Session = Depends(obter_sessao)):
    utente = sessao.get(Utente, dados.num_utente)
    if not utente or not verificar_palavra_passe(dados.pin_atual, utente.password_hash):
        raise HTTPException(status_code=401, detail="PIN atual incorreto")
    
    utente.password_hash = obter_hash_palavra_passe(dados.novo_pin)
    utente.primeiro_acesso = False
    sessao.add(utente)
    sessao.commit()
    
    return {"message": "PIN alterado com sucesso. Já pode aceder ao Portal e à App."}

@router.get("/utentes", response_model=List[Utente])
def ler_utentes(sessao: Session = Depends(obter_sessao)):
    utentes = sessao.exec(select(Utente)).all()
    return utentes

@router.post("/utentes/{num_utente}/resend-activation", dependencies=[Depends(admin_only)])
async def reenviar_ativacao_utente(num_utente: int, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(obter_utilizador_atual)):
    utente = sessao.get(Utente, num_utente)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    
    if not utente.email:
        raise HTTPException(status_code=400, detail="Este utente não tem e-mail registado. Por favor, atualize os dados primeiro.")
    
    # Removida restrição de conta ativa para permitir recuperação de PIN/Código

    # 1. Gerar novo PIN temporário
    pin_temporario = ''.join(random.choices(string.digits, k=6))
    
    # 2. Gerar novo código de ativação
    codigo_ativacao = f"{random.randint(100000, 999999)}"
    
    try:
        # Atualizar a password do utente para o novo PIN
        utente.password_hash = obter_hash_palavra_passe(pin_temporario)
        utente.primeiro_acesso = True
        sessao.add(utente)
        
        # Criar novo registro de validação
        validacao = EmailValidation(
            email=utente.email, 
            codigo=codigo_ativacao, 
            expira_em=datetime.now() + timedelta(hours=24)
        )
        sessao.add(validacao)
        sessao.commit()
        
        # Enviar e-mail
        background_tasks.add_task(enviar_email_ativacao, utente.email, utente.nome, f"{codigo_ativacao} (PIN Mobile: {pin_temporario})")
        
        log_audit(sessao, admin.id_utilizador, "RESEND_DATA", "utente", str(num_utente), f"Novo PIN e código enviados para {utente.email}")
        
        print(f"\n📧 [DEBUG REENVIO UTENTE] Utente {utente.num_utente} | Novo PIN: {pin_temporario} | Novo Código: {codigo_ativacao}\n")
        
        return {"message": "Novas credenciais de acesso enviadas com sucesso por e-mail."}
    except Exception as e:
        sessao.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar reenvio: {str(e)}")

@router.post("/utentes/{num_utente}/toggle-status", dependencies=[Depends(admin_only)])
def alternar_estado_utente(num_utente: int, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(obter_utilizador_atual)):
    utente = sessao.get(Utente, num_utente)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    
    # Alternar estado
    utente.ativo = not utente.ativo
    sessao.add(utente)
    sessao.commit()
    
    acao = "ACTIVATED" if utente.ativo else "SUSPENDED"
    log_audit(sessao, admin.id_utilizador, acao, "utente", str(num_utente), f"Estado do utente alterado para {'Ativo' if utente.ativo else 'Suspenso'}")
    
    return {"message": f"Utente {'reativado' if utente.ativo else 'suspenso'} com sucesso."}

@router.patch("/utentes/{num_utente}", response_model=Utente)
def atualizar_utente(
    num_utente: int, 
    utente_in: AtualizarUtente, 
    sessao: Session = Depends(obter_sessao),
    utilizador = Depends(RoleChecker(["ADMIN", "MEDICO", "ENFERMEIRO", "RECECIONISTA"]))
):
    db_utente = sessao.get(Utente, num_utente)
    if not db_utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    dados = utente_in.dict(exclude_unset=True)
    
    # Apenas ADMIN pode alterar o estado 'ativo'
    if "ativo" in dados and getattr(utilizador, "role_name", "") != "ADMIN":
        del dados["ativo"]

    for chave, valor in dados.items():
        setattr(db_utente, chave, valor)
    sessao.add(db_utente)
    sessao.commit()
    sessao.refresh(db_utente)
    return db_utente

@router.delete("/utentes/{num_utente}", dependencies=[Depends(admin_only)])
def eliminar_utente(num_utente: int, sessao: Session = Depends(obter_sessao)):
    db_utente = sessao.get(Utente, num_utente)
    if not db_utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    sessao.delete(db_utente)
    sessao.commit()
    return {"message": "Utente eliminado com sucesso"}

# PERFIL UTENTE (Self-service)
@router.get("/utentes/me", response_model=Utente)
def obter_meu_perfil_utente(utilizador = Depends(obter_utilizador_atual)):
    if getattr(utilizador, "role_name", None) != "UTENTE":
        raise HTTPException(status_code=403, detail="Apenas utentes podem aceder a este perfil")
    return utilizador

@router.patch("/utentes/me", response_model=Utente)
def atualizar_meu_perfil_utente(dados: AtualizarUtente, sessao: Session = Depends(obter_sessao), utilizador = Depends(obter_utilizador_atual)):
    if getattr(utilizador, "role_name", None) != "UTENTE":
        raise HTTPException(status_code=403, detail="Apenas utentes podem atualizar este perfil")
    
    # Obter o objeto da sessão para poder atualizar
    db_utente = sessao.get(Utente, utilizador.num_utente)
    
    update_data = dados.dict(exclude_unset=True)
    # Impedir que o utente mude o próprio estado de ativo (apenas admin)
    if "ativo" in update_data:
        del update_data["ativo"]
        
    # Tratar atualização de PIN/Password
    if "password" in update_data and update_data["password"]:
        # Atualizamos o hash e marcamos que já não é o primeiro acesso
        db_utente.password_hash = obter_hash_palavra_passe(update_data["password"])
        db_utente.primeiro_acesso = False
        del update_data["password"]

    for chave, valor in update_data.items():
        setattr(db_utente, chave, valor)
        
    sessao.add(db_utente)
    sessao.commit()
    sessao.refresh(db_utente)
    return db_utente

# EPISODIOS
@router.post("/episodes", response_model=EpisodioUrgencia)
def criar_episodio(dados_epis: CriarEpisodio, sessao: Session = Depends(obter_sessao), utilizador: Utilizador = Depends(obter_utilizador_atual)):
    # 1. Verificar se o utente já tem um episódio em aberto
    episodio_ativo = sessao.exec(
        select(EpisodioUrgencia).where(
            EpisodioUrgencia.id_utente == dados_epis.id_utente,
            EpisodioUrgencia.data_h_saida == None
        )
    ).first()

    if episodio_ativo:
        raise HTTPException(
            status_code=400,
            detail=f"O utente {dados_epis.id_utente} já possui um episódio de urgência em aberto (Código: {episodio_ativo.cod_epis}). Deve dar alta ao episódio anterior antes de registar um novo."
        )

    agora = datetime.now()
    data_entrada = dados_epis.data_h_entrada or agora
    
    # Gerar código automático: EP + YYYY + MM + SEQUENCIAL (4 dígitos)
    prefixo = f"EP{data_entrada.year}{data_entrada.month:02d}"
    
    # Buscar o último código com este prefixo
    query = select(EpisodioUrgencia.cod_epis).where(
        EpisodioUrgencia.cod_epis.like(f"{prefixo}%")
    ).order_by(EpisodioUrgencia.cod_epis.desc())
    
    ultimo_cod = sessao.exec(query).first()
    
    if ultimo_cod:
        try:
            sequencial = int(ultimo_cod[-4:]) + 1
        except (ValueError, TypeError):
            sequencial = 1
    else:
        sequencial = 1
    
    novo_cod_epis = f"{prefixo}{sequencial:04d}"

    db_episodio = EpisodioUrgencia(
        cod_epis=novo_cod_epis,
        data_h_entrada=data_entrada,
        id_utente=dados_epis.id_utente,
        id_hospital=dados_epis.id_hospital,
        sintomas=dados_epis.sintomas,
        observacoes=dados_epis.observacoes,
        id_utilizador_rececao=utilizador.id_utilizador
    )
    
    sessao.add(db_episodio)
    sessao.commit()
    sessao.refresh(db_episodio)
    return db_episodio

def obter_utilizador_opcional(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        return obter_utilizador_atual(token)
    except:
        return None

@router.get("/episodes", response_model=List[EpisodioUrgencia])
def ler_episodios(
    id_hospital: Optional[str] = None, 
    em_aberto: Optional[bool] = None,
    sessao: Session = Depends(obter_sessao),
    utilizador = Depends(obter_utilizador_opcional)
):
    query = select(EpisodioUrgencia)
    
    # Se houver um utilizador logado, verificar o seu papel na BD
    if utilizador:
        papel = sessao.get(PapelUtilizador, utilizador.id_role)
        nome_papel = papel.nome if papel else "USER"
        
        # Se for utente logado, filtrar obrigatoriamente pelos seus episódios
        if nome_papel == "UTENTE":
            query = query.where(EpisodioUrgencia.id_utente == utilizador.num_utente)
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    
    if em_aberto is True:
        query = query.where(EpisodioUrgencia.data_h_saida == None)
    elif em_aberto is False:
        query = query.where(EpisodioUrgencia.data_h_saida != None)
    
    query = query.order_by(EpisodioUrgencia.data_h_entrada.desc())
    
    episodios = sessao.exec(query).all()
    return episodios

@router.patch("/episodes/{cod_epis}", response_model=EpisodioUrgencia, dependencies=[Depends(admin_only)])
def atualizar_episodio(cod_epis: str, episodio_in: AtualizarEpisodio, sessao: Session = Depends(obter_sessao)):
    db_episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not db_episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    dados = episodio_in.dict(exclude_unset=True)
    for chave, valor in dados.items():
        setattr(db_episodio, chave, valor)
    sessao.add(db_episodio)
    sessao.commit()
    sessao.refresh(db_episodio)
    return db_episodio

@router.delete("/episodes/{cod_epis}", dependencies=[Depends(admin_only)])
def eliminar_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    db_episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not db_episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    sessao.delete(db_episodio)
    sessao.commit()
    return {"message": "Episódio eliminado com sucesso"}

@router.get("/episodes/{cod_epis}/team")
def obter_equipa_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    equipa = []
    
    # Triagem
    query_triagem = select(Triagem, Utilizador).join(
        Utilizador, Triagem.num_func_enfermeiro == Utilizador.num_func, isouter=True
    ).where(Triagem.cod_epis == cod_epis)
    triagens = sessao.exec(query_triagem).all()
    for t, u in triagens:
        equipa.append({
            "num_func": t.num_func_enfermeiro, 
            "nome": u.nome_completo if u else f"Profissional {t.num_func_enfermeiro}",
            "username": u.nome_utilizador if u else "---",
            "tipo_func": "ENFERMEIRO", 
            "papel": "Triagem", 
            "data": t.data_h_triagem
        })
        
    # Atos (via Envolve)
    query_atos = select(Envolve, Utilizador, FuncionarioHospital).join(
        FuncionarioHospital, Envolve.num_func == FuncionarioHospital.num_func
    ).join(
        Utilizador, Envolve.num_func == Utilizador.num_func, isouter=True
    ).where(Envolve.cod_epis == cod_epis)
    envolvimentos = sessao.exec(query_atos).all()
    for e, u, f in envolvimentos:
        equipa.append({
            "num_func": e.num_func, 
            "nome": u.nome_completo if u else f"Profissional {e.num_func}",
            "username": u.nome_utilizador if u else "---",
            "tipo_func": f.tipo_func, 
            "papel": "Ato Clínico", 
            "data": e.data_h_inicio
        })
        
    # Prescrições
    query_presc = select(Prescricao, Utilizador).join(
        Utilizador, Prescricao.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Prescricao.cod_epis == cod_epis)
    prescricoes = sessao.exec(query_presc).all()
    for p, u in prescricoes:
        equipa.append({
            "num_func": p.num_func_medico, 
            "nome": u.nome_completo if u else f"Médico {p.num_func_medico}",
            "username": u.nome_utilizador if u else "---",
            "tipo_func": "MEDICO", 
            "papel": "Prescrição", 
            "data": p.data_h_presc
        })

    # Internamento
    query_intern = select(Internamento, Utilizador).join(
        Utilizador, Internamento.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Internamento.cod_epis == cod_epis)
    internamentos = sessao.exec(query_intern).all()
    for i, u in internamentos:
        equipa.append({
            "num_func": i.num_func_medico,
            "nome": u.nome_completo if u else f"Médico {i.num_func_medico}",
            "username": u.nome_utilizador if u else "---",
            "tipo_func": "MEDICO",
            "papel": "Internamento (Médico Responsável)",
            "data": i.data_h_entrada
        })
        
    return equipa

@router.get("/episodes/{cod_epis}/journey")
def obter_percurso_episodio(
    cod_epis: str, 
    sessao: Session = Depends(obter_sessao),
    utilizador = Depends(obter_utilizador_atual)
):
    episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    
    # Validar Permissões
    role = getattr(utilizador, "role_name", "USER")
    if role == "UTENTE":
        if episodio.id_utente != utilizador.num_utente:
            raise HTTPException(status_code=403, detail="Não tem permissão para aceder a este episódio")
    elif role != "ADMIN":
        # Se não for admin nem o próprio utente, bloquear (comportamento original era admin_only)
        raise HTTPException(status_code=403, detail="Apenas administradores podem aceder ao percurso global")

    utente = sessao.get(Utente, episodio.id_utente)
    
    # Triagem com LEFT JOIN
    query_triagem = select(Triagem, Utilizador).join(
        Utilizador, Triagem.num_func_enfermeiro == Utilizador.num_func, isouter=True
    ).where(Triagem.cod_epis == cod_epis)
    res_triagem = sessao.exec(query_triagem).first()
    triagem_final = None
    if res_triagem:
        t, u = res_triagem
        triagem_final = t.dict()
        triagem_final["enfermeiro_nome"] = u.nome_completo if u else f"Enf. {t.num_func_enfermeiro}"
        triagem_final["enfermeiro_username"] = u.nome_utilizador if u else "---"

    # Atos com LEFT JOIN
    query_atos = select(Ato, Utilizador).join(
        Utilizador, Ato.num_func == Utilizador.num_func, isouter=True
    ).where(Ato.cod_epis == cod_epis)
    res_atos = sessao.exec(query_atos).all()
    atos_finais = []
    for a, u in res_atos:
        ato_dict = a.dict()
        ato_dict["profissional_nome"] = u.nome_completo if u else f"Prof. {a.num_func}"
        ato_dict["profissional_username"] = u.nome_utilizador if u else "---"
        atos_finais.append(ato_dict)

    # Prescrições com LEFT JOIN
    query_presc = select(Prescricao, Utilizador).join(
        Utilizador, Prescricao.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Prescricao.cod_epis == cod_epis)
    res_presc = sessao.exec(query_presc).all()
    presc_finais = []
    for p, u in res_presc:
        presc_dict = p.dict()
        presc_dict["medico_nome"] = u.nome_completo if u else f"Dr. {p.num_func_medico}"
        presc_dict["medico_username"] = u.nome_utilizador if u else "---"
        presc_finais.append(presc_dict)

    # Internamento com LEFT JOIN
    query_intern = select(Internamento, Utilizador).join(
        Utilizador, Internamento.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Internamento.cod_epis == cod_epis)
    res_intern = sessao.exec(query_intern).first()
    intern_final = None
    if res_intern:
        i, u = res_intern
        intern_final = i.dict()
        intern_final["medico_nome"] = u.nome_completo if u else f"Dr. {i.num_func_medico}"
        intern_final["medico_username"] = u.nome_utilizador if u else "---"
        
    equipa = obter_equipa_episodio(cod_epis, sessao)
    
    # Logs de auditoria relacionados a este episódio
    logs = sessao.exec(select(AuditLog).where(AuditLog.id_recurso == cod_epis)).all()
    
    return {
        "episodio": episodio,
        "utente": utente,
        "triagem": triagem_final,
        "atos": atos_finais,
        "prescricoes": presc_finais,
        "internamento": intern_final,
        "equipa": equipa,
        "logs_auditoria": logs
    }

@router.get("/episodes/awaiting-triage")
def ler_episodios_aguardando_triagem(
    id_hospital: Optional[str] = None, 
    sessao: Session = Depends(obter_sessao)
):
    # Selecionar episódios que não têm triagem e não têm data de saída
    query = select(EpisodioUrgencia, Utilizador).join(
        Utilizador, EpisodioUrgencia.id_utilizador_rececao == Utilizador.id_utilizador, isouter=True
    ).where(
        EpisodioUrgencia.data_h_saida == None,
        ~EpisodioUrgencia.cod_epis.in_(select(Triagem.cod_epis))
    )
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    
    # Ordem de chegada (mais antigos primeiro)
    query = query.order_by(EpisodioUrgencia.data_h_entrada.asc())
    
    resultados = sessao.exec(query).all()
    
    final = []
    for ep, user in resultados:
        ep_dict = ep.dict()
        ep_dict["rececionista_nome"] = user.nome_completo if user else f"Utilizador {ep.id_utilizador_rececao}"
        ep_dict["rececionista_username"] = user.nome_utilizador if user else "---"
        final.append(ep_dict)
        
    return final

# TRIAGEM
@router.post("/triagens", response_model=Triagem)
def criar_triagem(triagem: Triagem, sessao: Session = Depends(obter_sessao)):
    sessao.add(triagem)
    sessao.commit()
    sessao.refresh(triagem)
    return triagem

@router.get("/episodes/awaiting-doctor", response_model=List[dict])
def ler_episodios_aguardando_medico(
    id_hospital: Optional[str] = None, 
    sessao: Session = Depends(obter_sessao)
):
    print(f"DEBUG: ler_episodios_aguardando_medico chamado com id_hospital='{id_hospital}'")
    
    # Selecionar episódios que TÊM triagem e NÃO têm data de saída
    query = select(EpisodioUrgencia, Triagem, Utente).join(
        Triagem, EpisodioUrgencia.cod_epis == Triagem.cod_epis
    ).join(
        Utente, EpisodioUrgencia.id_utente == Utente.num_utente
    ).where(
        EpisodioUrgencia.data_h_saida == None
    )
    
    if id_hospital and id_hospital.strip() and id_hospital != "undefined" and id_hospital != "null":
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
        print(f"DEBUG: Filtrando por hospital '{id_hospital}'")
    else:
        print("DEBUG: Sem filtro de hospital (retornando todos)")
    
    # Ordenar por prioridade (Simulação simplificada Manchester) e depois por tempo
    resultados = sessao.exec(query).all()
    
    # Transformar em lista de dicts para facilitar o frontend
    fila = []
    for ep, tri, ut in resultados:
        fila.append({
            "cod_epis": ep.cod_epis,
            "data_h_entrada": ep.data_h_entrada,
            "utente_nome": ut.nome,
            "prioridade": tri.prioridade,
            "sintomas": tri.sintomas
        })
    
    # Ordenação lógica: Vermelho > Laranja > Amarelo > Verde > Azul
    ordem = {"VERMELHO": 0, "LARANJA": 1, "AMARELO": 2, "VERDE": 3, "AZUL": 4}
    fila.sort(key=lambda x: (ordem.get(x["prioridade"], 9), x["data_h_entrada"]))
    
    print(f"DEBUG: Fila para hospital '{id_hospital}' tem {len(fila)} pacientes.")
    
    return fila

@router.get("/episodes/{cod_epis}")
def obter_episodio_detalhado(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    utente = sessao.get(Utente, episodio.id_utente)
    
    # Triagem com nome do enfermeiro (LEFT JOIN)
    query_triagem = select(Triagem, Utilizador).join(
        Utilizador, Triagem.num_func_enfermeiro == Utilizador.num_func, isouter=True
    ).where(Triagem.cod_epis == cod_epis)
    res_triagem = sessao.exec(query_triagem).first()
    
    triagem_data = None
    if res_triagem:
        t, u = res_triagem
        triagem_data = t.dict()
        triagem_data["enfermeiro_nome"] = u.nome_completo if u else f"Enf. {t.num_func_enfermeiro}"

    return {
        "cod_epis": episodio.cod_epis,
        "data_h_entrada": episodio.data_h_entrada,
        "id_utente": episodio.id_utente,
        "id_hospital": episodio.id_hospital,
        "sintomas_iniciais": episodio.sintomas,
        "utente": utente,
        "triagem": triagem_data
    }

@router.get("/hospitals/{nome_hosp}/services", response_model=List[ServicoHospitalar])
def listar_servicos_hospital(nome_hosp: str, sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(ServicoHospitalar).where(ServicoHospitalar.id_hosp == nome_hosp)).all()

@router.post("/internamentos", response_model=Internamento)
def criar_internamento(internamento: Internamento, sessao: Session = Depends(obter_sessao)):
    sessao.add(internamento)
    
    # Ao internar, o episódio de urgência termina
    episodio = sessao.get(EpisodioUrgencia, internamento.cod_epis)
    if episodio:
        episodio.data_h_saida = datetime.now()
        sessao.add(episodio)
    
    sessao.commit()
    sessao.refresh(internamento)
    return internamento

@router.post("/triagens/manchester", response_model=Triagem)
def registar_triagem_manchester(dados: CriarTriagem, sessao: Session = Depends(obter_sessao)):
    # 1. Validar episódio
    episodio = sessao.get(EpisodioUrgencia, dados.cod_epis)
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    
    # 2. Lógica de Manchester (Prioridade baseada em sinais vitais)
    prioridade = "AZUL" 
    temp = dados.temperatura
    
    try:
        sistolica = int(dados.tensao_arterial.split('/')[0])
    except:
        sistolica = 120

    if temp >= 40 or sistolica < 70:
        prioridade = "VERMELHO"
    elif temp >= 39 or sistolica > 190 or sistolica < 90:
        prioridade = "LARANJA"
    elif temp >= 38 or sistolica > 160:
        prioridade = "AMARELO"
    elif temp >= 37.5:
        prioridade = "VERDE"
    
    db_triagem = Triagem(
        cod_epis=dados.cod_epis,
        prioridade=prioridade,
        tensao_arterial=dados.tensao_arterial,
        temperatura=dados.temperatura,
        sintomas=dados.sintomas,
        observacoes=dados.observacoes,
        num_func_enfermeiro=dados.num_func_enfermeiro,
        data_h_triagem=datetime.now()
    )
    
    sessao.add(db_triagem)
    sessao.commit()
    sessao.refresh(db_triagem)
    return db_triagem

@router.get("/utentes/{num_utente}/history")
def obter_historico_utente(num_utente: int, sessao: Session = Depends(obter_sessao), utilizador = Depends(obter_utilizador_atual)):
    # Validar se o utilizador tem permissão (Médico, Enfermeiro, Admin ou o próprio Utente)
    role = getattr(utilizador, "role_name", "USER")
    
    if role == "UTENTE":
        if int(utilizador.num_utente) != num_utente:
            raise HTTPException(status_code=403, detail="Apenas pode aceder ao seu próprio histórico")
    elif role not in ["ADMIN", "MEDICO", "ENFERMEIRO"]:
        raise HTTPException(status_code=403, detail="Não tem permissão para aceder a este histórico")
    
    # 1. Obter todos os episódios do utente
    episodios = sessao.exec(
        select(EpisodioUrgencia).where(EpisodioUrgencia.id_utente == num_utente).order_by(EpisodioUrgencia.data_h_entrada.desc())
    ).all()
    
    historico = []
    for ep in episodios:
        # Triagem com nome (LEFT JOIN)
        query_triagem = select(Triagem, Utilizador).join(
            Utilizador, Triagem.num_func_enfermeiro == Utilizador.num_func, isouter=True
        ).where(Triagem.cod_epis == ep.cod_epis)
        res_triagem = sessao.exec(query_triagem).first()
        triagem_final = None
        if res_triagem:
            t, u = res_triagem
            triagem_final = t.dict()
            triagem_final["enfermeiro_nome"] = u.nome_completo if u else f"Enf. {t.num_func_enfermeiro}"
            triagem_final["enfermeiro_username"] = u.nome_utilizador if u else "---"

        # Atos com nome (LEFT JOIN)
        query_atos = select(Ato, Utilizador).join(
            Utilizador, Ato.num_func == Utilizador.num_func, isouter=True
        ).where(Ato.cod_epis == ep.cod_epis)
        res_atos = sessao.exec(query_atos).all()
        atos_finais = []
        for a, u in res_atos:
            ato_dict = a.dict()
            ato_dict["profissional_nome"] = u.nome_completo if u else f"Prof. {a.num_func}"
            ato_dict["profissional_username"] = u.nome_utilizador if u else "---"
            atos_finais.append(ato_dict)

        # Prescrições com nome (LEFT JOIN)
        query_presc = select(Prescricao, Utilizador).join(
            Utilizador, Prescricao.num_func_medico == Utilizador.num_func, isouter=True
        ).where(Prescricao.cod_epis == ep.cod_epis)
        res_presc = sessao.exec(query_presc).all()
        presc_finais = []
        for p, u in res_presc:
            presc_dict = p.dict()
            presc_dict["medico_nome"] = u.nome_completo if u else f"Dr. {p.num_func_medico}"
            presc_dict["medico_username"] = u.nome_utilizador if u else "---"
            presc_finais.append(presc_dict)

        # Internamento com nome (LEFT JOIN)
        query_intern = select(Internamento, Utilizador).join(
            Utilizador, Internamento.num_func_medico == Utilizador.num_func, isouter=True
        ).where(Internamento.cod_epis == ep.cod_epis)
        res_intern = sessao.exec(query_intern).first()
        intern_final = None
        if res_intern:
            i, u = res_intern
            intern_final = i.dict()
            intern_final["medico_nome"] = u.nome_completo if u else f"Dr. {i.num_func_medico}"
            intern_final["medico_username"] = u.nome_utilizador if u else "---"
        
        historico.append({
            "episodio": ep,
            "triagem": triagem_final,
            "atos": atos_finais,
            "prescricoes": presc_finais,
            "internamento": intern_final
        })
    
    return historico

@router.get("/episodes/{cod_epis}/prescriptions", response_model=List[Prescricao])
def listar_prescricoes_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(Prescricao).where(Prescricao.cod_epis == cod_epis)).all()

# ATOS
@router.post("/atos", response_model=Ato)
def criar_ato(ato: Ato, sessao: Session = Depends(obter_sessao)):
    sessao.add(ato)
    
    # Registar na tabela original ENVOLVE
    db_envolve = Envolve(
        data_h_inicio=ato.data_h_inicio,
        num_func=ato.num_func,
        cod_epis=ato.cod_epis,
        id_hosp=ato.id_hosp
    )
    sessao.add(db_envolve)
    
    # Se a decisão clínica for ALTA, fechar o episódio
    if ato.decisao_clinica == "ALTA":
        episodio = sessao.get(EpisodioUrgencia, ato.cod_epis)
        if episodio:
            episodio.data_h_saida = datetime.now()
            sessao.add(episodio)
            
    sessao.commit()
    sessao.refresh(ato)
    return ato

@router.get("/internamentos")
def listar_internamentos(id_hospital: Optional[str] = None, em_aberto: bool = True, sessao: Session = Depends(obter_sessao)):
    query = select(Internamento, EpisodioUrgencia, Utente, ServicoHospitalar).join(
        EpisodioUrgencia, Internamento.cod_epis == EpisodioUrgencia.cod_epis
    ).join(
        Utente, EpisodioUrgencia.id_utente == Utente.num_utente
    ).join(
        ServicoHospitalar, Internamento.id_servico == ServicoHospitalar.id_servico
    )
    
    if em_aberto:
        query = query.where(Internamento.data_h_saida == None)
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
        
    resultados = sessao.exec(query).all()
    
    internamentos_formatados = []
    for intern, ep, ut, serv in resultados:
        # Obter nome do médico responsável
        medico_nome = "---"
        if intern.num_func_medico:
            u_medico = sessao.exec(select(Utilizador).where(Utilizador.num_func == intern.num_func_medico)).first()
            if u_medico:
                medico_nome = u_medico.nome_completo

        internamentos_formatados.append({
            "num_internamento": intern.num_internamento,
            "cod_epis": intern.cod_epis,
            "utente_nome": ut.nome,
            "id_utente": ut.num_utente,
            "servico_nome": serv.nome,
            "num_cama": intern.num_cama,
            "data_h_entrada": intern.data_h_entrada,
            "medico_responsavel": medico_nome
        })
        
    return internamentos_formatados

@router.post("/internamentos/{num_internamento}/discharge")
def dar_alta_internamento(num_internamento: int, sessao: Session = Depends(obter_sessao)):
    internamento = sessao.get(Internamento, num_internamento)
    if not internamento:
        raise HTTPException(status_code=404, detail="Internamento não encontrado")
    
    agora = datetime.now()
    internamento.data_h_saida = agora
    sessao.add(internamento)
    
    # Também fechar o episódio de urgência (se ainda estiver aberto por algum motivo)
    episodio = sessao.get(EpisodioUrgencia, internamento.cod_epis)
    if episodio and episodio.data_h_saida is None:
        episodio.data_h_saida = agora
        sessao.add(episodio)
        
    sessao.commit()
    return {"message": "Alta de internamento registada"}

# PRESCRICAO
@router.post("/prescricoes", response_model=Prescricao)
def criar_prescricao(prescricao: Prescricao, sessao: Session = Depends(obter_sessao)):
    sessao.add(prescricao)
    sessao.commit()
    sessao.refresh(prescricao)
    return prescricao

# DISCHARGE
@router.post("/episodes/{cod_epis}/discharge")
def dar_alta(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    episodio.data_h_saida = datetime.now()
    sessao.add(episodio)
    sessao.commit()
    return {"message": "Paciente teve alta"}
