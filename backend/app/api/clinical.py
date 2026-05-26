from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlmodel import Session, select, func, union_all, or_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, timezone, date
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

@router.get("/triagens", dependencies=[Depends(admin_only)])
def listar_triagens(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    query = select(Triagem, Utilizador).join(
        Utilizador, or_(Triagem.num_func_enfermeiro == Utilizador.num_func, Triagem.num_func_enfermeiro == Utilizador.id_utilizador), isouter=True
    )
    if id_hospital:
        query = query.join(EpisodioUrgencia, Triagem.cod_epis == EpisodioUrgencia.cod_epis).where(EpisodioUrgencia.id_hospital == id_hospital)
    
    resultados = sessao.exec(query).all()
    final = []
    for t, u in resultados:
        t_dict = t.dict()
        t_dict["enfermeiro_nome"] = u.nome_completo if u else f"Enf. {t.num_func_enfermeiro}"
        t_dict["enfermeiro_username"] = u.nome_utilizador if u else "---"
        final.append(t_dict)
    return final

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

@router.get("/atos", dependencies=[Depends(admin_only)])
def listar_atos(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    query = select(Ato, Utilizador).join(
        Utilizador, or_(Ato.num_func == Utilizador.num_func, Ato.num_func == Utilizador.id_utilizador), isouter=True
    )
    if id_hospital:
        query = query.where(Ato.id_hosp == id_hospital)
        
    resultados = sessao.exec(query).all()
    final = []
    for a, u in resultados:
        a_dict = a.dict()
        a_dict["profissional_nome"] = u.nome_completo if u else f"Prof. {a.num_func}"
        a_dict["profissional_username"] = u.nome_utilizador if u else "---"
        final.append(a_dict)
    return final

@router.patch("/atos/{id_ato}/audit", response_model=Ato, dependencies=[Depends(admin_only)])
def atualizar_ato_auditado(
    id_ato: int, 
    dados: AtualizarAtoAuditado, 
    request: Request,
    sessao: Session = Depends(obter_sessao),
    admin: Utilizador = Depends(obter_utilizador_atual)
):
    db_ato = sessao.get(Ato, id_ato)
    if not db_ato:
        raise HTTPException(status_code=404, detail="Ato clínico não encontrado")
    
    detalhes = f"Justificativa: {dados.justificativa} | Autorização: {dados.autorizacao}"
    log_audit(sessao, admin.id_utilizador, "UPDATE_AUDITED", "ato", str(id_ato), detalhes, request)
    
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
    
    # VERIFICAÇÃO DE USO
    # 1. Verificar episódios vinculados a este hospital
    if sessao.exec(select(EpisodioUrgencia).where(EpisodioUrgencia.id_hospital == nome_hosp)).first():
        raise HTTPException(status_code=400, detail=f"Não é possível eliminar o hospital '{nome_hosp}' porque existem episódios de urgência registados nesta unidade. O histórico deve ser preservado para fins de auditoria.")

    # 2. Verificar serviços vinculados
    if sessao.exec(select(ServicoHospitalar).where(ServicoHospitalar.id_hosp == nome_hosp)).first():
        raise HTTPException(status_code=400, detail="Este hospital possui serviços configurados e ativos. Remova os serviços antes de tentar eliminar a unidade, se aplicável.")

    sessao.delete(db_hospital)
    sessao.commit()
    return {"message": "Hospital eliminado com sucesso"}

# UTENTE
@router.get("/utentes/search", response_model=List[Utente])
def pesquisar_utente(
    num_utente: Optional[int] = None, 
    telemovel: Optional[str] = None, 
    nome: Optional[str] = None,
    sessao: Session = Depends(obter_sessao)
):
    query = select(Utente)
    if num_utente:
        query = query.where(Utente.num_utente == num_utente)
    elif telemovel:
        # Pesquisa parcial por telemóvel
        query = query.where(Utente.telemovel.like(f"%{telemovel}%"))
    elif nome:
        # Pesquisa parcial por nome (case-insensitive)
        query = query.where(func.lower(Utente.nome).like(f"%{nome.lower()}%"))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Deve fornecer um critério de pesquisa (NIF, Telemóvel ou Nome)."
        )
    
    # Limitar resultados para performance
    resultados = sessao.exec(query.limit(10)).all()
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

    # 5. Gerar PIN único para Ativação e Primeiro Acesso (6 dígitos)
    pin_unico = ''.join(random.choices(string.digits, k=6))
    
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
        password_hash=obter_hash_palavra_passe(pin_unico),
        ativo=False,
        primeiro_acesso=True,
        parentesco=dados.parentesco,
        id_role=papel_utente.id_role
    )
    
    try:
        sessao.add(novo_utente)
        validacao = EmailValidation(
            email=novo_utente.email, 
            codigo=pin_unico, 
            expira_em=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        sessao.add(validacao)
        sessao.commit()
        
        # 7. Enviar e-mail com o PIN único
        background_tasks.add_task(enviar_email_ativacao, novo_utente.email, novo_utente.nome, pin_unico)
        
        print(f"\n📧 [DEBUG MOBILE] Utente {novo_utente.num_utente} | PIN Único: {pin_unico}\n")
        
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
            expira_em=datetime.now(timezone.utc) + timedelta(hours=24)
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
    
    # VERIFICAÇÃO DE USO
    # 1. Verificar episódios vinculados
    episodio_existente = sessao.exec(select(EpisodioUrgencia).where(EpisodioUrgencia.id_utente == num_utente)).first()
    if episodio_existente:
        raise HTTPException(
            status_code=400,
            detail="Não é possível eliminar este utente porque já possui histórico de episódios de urgência no sistema. Para garantir a coerência e estabilidade da base de dados, o registo deve ser preservado."
        )
    
    # 2. Verificar logs de auditoria (se houver)
    log_existente = sessao.exec(select(AuditLog).where(AuditLog.recurso == "utente", AuditLog.id_recurso == str(num_utente))).first()
    if log_existente:
        raise HTTPException(
            status_code=400,
            detail="Este utente está interligado a registos de auditoria do sistema. A sua remoção comprometeria a integridade dos dados históricos."
        )

    # Limpar validações pendentes se houver
    sessao.execute(text("DELETE FROM email_validation WHERE email = :email"), {"email": db_utente.email})

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

    agora = datetime.now(timezone.utc)
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

@router.get("/episodes")
def ler_episodios(
    id_hospital: Optional[str] = None, 
    em_aberto: Optional[bool] = None,
    sessao: Session = Depends(obter_sessao),
    utilizador = Depends(obter_utilizador_opcional)
):
    query = select(EpisodioUrgencia, Utilizador).join(
        Utilizador, EpisodioUrgencia.id_utilizador_rececao == Utilizador.id_utilizador, isouter=True
    )
    
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
    
    resultados = sessao.exec(query).all()
    
    final = []
    for ep, user in resultados:
        ep_dict = ep.dict()
        ep_dict["profissional_info"] = {
            "nome": user.nome_completo if user else "Utilizador Desconhecido",
            "username": user.nome_utilizador if user else "---",
            "num_func": user.num_func if user else (ep.id_utilizador_rececao or "---")
        }
        final.append(ep_dict)
        
    return final

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
    
    # VERIFICAÇÃO DE USO
    # 1. Verificar triagem
    if sessao.exec(select(Triagem).where(Triagem.cod_epis == cod_epis)).first():
        raise HTTPException(status_code=400, detail="Este episódio já possui uma triagem registada e não pode ser eliminado para manter a integridade dos dados clínicos.")
    
    # 2. Verificar atos clínicos
    if sessao.exec(select(Ato).where(Ato.cod_epis == cod_epis)).first():
        raise HTTPException(status_code=400, detail="Não é possível eliminar este episódio porque existem atos clínicos interligados. O registo é necessário para o histórico do sistema.")

    # 3. Verificar prescrições
    if sessao.exec(select(Prescricao).where(Prescricao.cod_epis == cod_epis)).first():
        raise HTTPException(status_code=400, detail="Este episódio contém prescrições médicas registadas e está usado no sistema. A remoção não é permitida por motivos de estabilidade e auditoria.")

    # 4. Verificar internamento
    if sessao.exec(select(Internamento).where(Internamento.cod_epis == cod_epis)).first():
        raise HTTPException(status_code=400, detail="Este episódio resultou num internamento interligado. Para garantir a coerência da base de dados, o registo deve ser preservado.")

    sessao.delete(db_episodio)
    sessao.commit()
    return {"message": "Episódio eliminado com sucesso"}

@router.get("/episodes/{cod_epis}/team")
def obter_equipa_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    equipa_dict = {} # Usar dict para evitar duplicados por num_func
    
    # 1. Triagem (Enfermeiro)
    try:
        query_triagem = select(Triagem, Utilizador).join(
            Utilizador, or_(Triagem.num_func_enfermeiro == Utilizador.num_func, Triagem.num_func_enfermeiro == Utilizador.id_utilizador), isouter=True
        ).where(Triagem.cod_epis == cod_epis)
        triagens = sessao.exec(query_triagem).all()
        for t, u in triagens:
            n_func = t.num_func_enfermeiro
            equipa_dict[n_func] = {
                "num_func": n_func, 
                "nome": u.nome_completo if u else f"Profissional {n_func}",
                "username": u.nome_utilizador if u else "---",
                "tipo_func": "ENFERMEIRO", 
                "papel": "Triagem", 
                "data": t.data_h_triagem
            }
    except Exception as e:
        print(f"DEBUG TEAM: Erro na triagem: {str(e)}")
        sessao.rollback()

    # 2. Atos Clínicos - Profissional Principal (Ato.num_func)
    try:
        query_atos_principal = select(Ato, Utilizador, FuncionarioHospital).join(
            FuncionarioHospital, Ato.num_func == FuncionarioHospital.num_func
        ).join(
            Utilizador, or_(Ato.num_func == Utilizador.num_func, Ato.num_func == Utilizador.id_utilizador), isouter=True
        ).where(Ato.cod_epis == cod_epis)
        
        atos_principais = sessao.exec(query_atos_principal).all()
        for a, u, f in atos_principais:
            n_func = a.num_func
            equipa_dict[n_func] = {
                "num_func": n_func, 
                "nome": u.nome_completo if u else f"Profissional {n_func}",
                "username": u.nome_utilizador if u else "---",
                "tipo_func": f.tipo_func, 
                "papel": f"Ato Clínico ({a.tipo})", 
                "data": a.data_h_inicio
            }
    except Exception as e:
        print(f"DEBUG TEAM: Erro na triagem: {str(e)}")
        sessao.rollback()

    # 3. Atos Clínicos - Profissionais Envolvidos (via Envolve)
    try:
        query_envolve = select(Envolve, Utilizador, FuncionarioHospital, Ato).join(
            Ato, Envolve.id_ato == Ato.id_ato
        ).join(
            FuncionarioHospital, Envolve.num_func == FuncionarioHospital.num_func
        ).join(
            Utilizador, or_(Envolve.num_func == Utilizador.num_func, Envolve.num_func == Utilizador.id_utilizador), isouter=True
        ).where(Ato.cod_epis == cod_epis)
        
        envolvimentos = sessao.exec(query_envolve).all()
        for env, u, f, a in envolvimentos:
            n_func = env.num_func
            if n_func not in equipa_dict:
                equipa_dict[n_func] = {
                    "num_func": n_func, 
                    "nome": u.nome_completo if u else f"Profissional {n_func}",
                    "username": u.nome_utilizador if u else "---",
                    "tipo_func": f.tipo_func, 
                    "papel": f"Apoio em Ato ({a.tipo})", 
                    "data": a.data_h_inicio
                }
    except Exception as e:
        print(f"DEBUG TEAM: Erro nos envolvimentos: {str(e)}")
        sessao.rollback()

    # 4. Prescrições (Médico)
    try:
        query_presc = select(Prescricao, Utilizador).join(
            Utilizador, or_(Prescricao.num_func_medico == Utilizador.num_func, Prescricao.num_func_medico == Utilizador.id_utilizador), isouter=True
        ).where(Prescricao.cod_epis == cod_epis)
        prescricoes = sessao.exec(query_presc).all()
        for p, u in prescricoes:
            n_func = p.num_func_medico
            if n_func not in equipa_dict:
                equipa_dict[n_func] = {
                    "num_func": n_func, 
                    "nome": u.nome_completo if u else f"Médico {n_func}",
                    "username": u.nome_utilizador if u else "---",
                    "tipo_func": "MEDICO", 
                    "papel": "Prescrição", 
                    "data": p.data_h_presc
                }
    except Exception as e:
        print(f"DEBUG TEAM: Erro nas prescrições: {str(e)}")
        sessao.rollback()

    # 5. Internamento (Médico Responsável)
    try:
        query_intern = select(Internamento, Utilizador).join(
            Utilizador, or_(Internamento.num_func_medico == Utilizador.num_func, Internamento.num_func_medico == Utilizador.id_utilizador), isouter=True
        ).where(Internamento.cod_epis == cod_epis)
        internamentos = sessao.exec(query_intern).all()
        for i, u in internamentos:
            n_func = i.num_func_medico
            if n_func not in equipa_dict:
                equipa_dict[n_func] = {
                    "num_func": n_func,
                    "nome": u.nome_completo if u else f"Médico {n_func}",
                    "username": u.nome_utilizador if u else "---",
                    "tipo_func": "MEDICO",
                    "papel": "Internamento (Médico Responsável)",
                    "data": i.data_h_entrada
                }
    except Exception as e:
        print(f"DEBUG TEAM: Erro no internamento: {str(e)}")
        sessao.rollback()
        
    # Converter para lista e ordenar por data
    equipa = list(equipa_dict.values())
    equipa.sort(key=lambda x: x["data"] if x["data"] else datetime.min, reverse=True)
    
    return equipa

@router.get("/episodes/{cod_epis}/journey")
def obter_percurso_episodio(
    cod_epis: str, 
    sessao: Session = Depends(obter_sessao),
    utilizador = Depends(obter_utilizador_atual)
):
    try:
        # 1. Episódio e Rececionista
        query_ep = select(EpisodioUrgencia, Utilizador).join(
            Utilizador, EpisodioUrgencia.id_utilizador_rececao == Utilizador.id_utilizador, isouter=True
        ).where(EpisodioUrgencia.cod_epis == cod_epis)
        
        res_ep = sessao.exec(query_ep).first()
        if not res_ep:
            raise HTTPException(status_code=404, detail="Episódio não encontrado")
        
        episodio, rececionista = res_ep
        utente = sessao.get(Utente, episodio.id_utente)
        
        ep_dict = episodio.dict()
        # Campos de compatibilidade
        ep_dict["rececionista_nome"] = rececionista.nome_completo if rececionista else "Desconhecido"
        ep_dict["rececionista_username"] = rececionista.nome_utilizador if rececionista else "---"
        # Novo padrão uniforme
        ep_dict["profissional_info"] = {
            "nome": ep_dict["rececionista_nome"],
            "username": ep_dict["rececionista_username"],
            "num_func": rececionista.num_func if rececionista else (episodio.id_utilizador_rececao or "---")
        }

        # 2. Triagem
        query_triagem = select(Triagem, Utilizador).join(
            Utilizador, or_(Triagem.num_func_enfermeiro == Utilizador.num_func, Triagem.num_func_enfermeiro == Utilizador.id_utilizador), isouter=True
        ).where(Triagem.cod_epis == cod_epis)
        res_triagem = sessao.exec(query_triagem).first()
        
        triagem_final = None
        if res_triagem:
            t, u = res_triagem
            triagem_final = t.dict()
            triagem_final["enfermeiro_nome"] = u.nome_completo if u else f"Enfermeiro {t.num_func_enfermeiro}"
            triagem_final["enfermeiro_username"] = u.nome_utilizador if u else "---"
            triagem_final["profissional_info"] = {
                "nome": triagem_final["enfermeiro_nome"],
                "username": triagem_final["enfermeiro_username"],
                "num_func": t.num_func_enfermeiro
            }

        # 3. Atos (Ordenados cronologicamente)
        query_atos = select(Ato, Utilizador).join(
            Utilizador, or_(Ato.num_func == Utilizador.num_func, Ato.num_func == Utilizador.id_utilizador), isouter=True
        ).where(Ato.cod_epis == cod_epis).order_by(Ato.data_h_inicio.asc())
        res_atos = sessao.exec(query_atos).all()
        atos_finais = []
        for a, u in res_atos:
            ato_dict = a.dict()
            ato_dict["profissional_nome"] = u.nome_completo if u else f"Profissional {a.num_func}"
            ato_dict["profissional_username"] = u.nome_utilizador if u else "---"
            ato_dict["profissional_info"] = {
                "nome": ato_dict["profissional_nome"],
                "username": ato_dict["profissional_username"],
                "num_func": a.num_func
            }
            atos_finais.append(ato_dict)

        # 4. Prescrições (Ordenadas cronologicamente)
        query_presc = select(Prescricao, Utilizador).join(
            Utilizador, or_(Prescricao.num_func_medico == Utilizador.num_func, Prescricao.num_func_medico == Utilizador.id_utilizador), isouter=True
        ).where(Prescricao.cod_epis == cod_epis).order_by(Prescricao.data_h_presc.asc())
        res_presc = sessao.exec(query_presc).all()
        presc_finais = []
        for p, u in res_presc:
            presc_dict = p.dict()
            presc_dict["medico_nome"] = u.nome_completo if u else f"Médico {p.num_func_medico}"
            presc_dict["medico_username"] = u.nome_utilizador if u else "---"
            presc_dict["profissional_info"] = {
                "nome": presc_dict["medico_nome"],
                "username": presc_dict["medico_username"],
                "num_func": p.num_func_medico
            }
            presc_finais.append(presc_dict)

        # 5. Internamento
        query_intern = select(Internamento, Utilizador).join(
            Utilizador, or_(Internamento.num_func_medico == Utilizador.num_func, Internamento.num_func_medico == Utilizador.id_utilizador), isouter=True
        ).where(Internamento.cod_epis == cod_epis)
        res_intern = sessao.exec(query_intern).first()
        intern_final = None
        if res_intern:
            i, u = res_intern
            intern_final = i.dict()
            intern_final["medico_nome"] = u.nome_completo if u else f"Médico {i.num_func_medico}"
            intern_final["medico_username"] = u.nome_utilizador if u else "---"
            intern_final["profissional_info"] = {
                "nome": intern_final["medico_nome"],
                "username": intern_final["medico_username"],
                "num_func": i.num_func_medico
            }
            
        return {
            "episodio": ep_dict,
            "utente": utente,
            "triagem": triagem_final,
            "atos": atos_finais,
            "prescricoes": presc_finais,
            "internamento": intern_final,
            "equipa": obter_equipa_episodio(cod_epis, sessao)
        }
    except Exception as e:
        print(f"ERRO JOURNEY: {str(e)}")
        sessao.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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
    
    # Ordem de chegada (mais recentes primeiro)
    query = query.order_by(EpisodioUrgencia.data_h_entrada.desc())
    
    resultados = sessao.exec(query).all()
    
    final = []
    for ep, user in resultados:
        ep_dict = ep.dict()
        ep_dict["rececionista_nome"] = user.nome_completo if user else f"Utilizador {ep.id_utilizador_rececao}"
        ep_dict["rececionista_username"] = user.nome_utilizador if user else "---"
        ep_dict["profissional_info"] = {
            "nome": ep_dict["rececionista_nome"],
            "username": ep_dict["rececionista_username"],
            "num_func": user.num_func if user else (ep.id_utilizador_rececao or "---")
        }
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
    # Dentro da mesma prioridade, mostrar os mais recentes primeiro conforme solicitado
    ordem = {"VERMELHO": 0, "LARANJA": 1, "AMARELO": 2, "VERDE": 3, "AZUL": 4}
    fila.sort(key=lambda x: (ordem.get(x["prioridade"], 9), x["data_h_entrada"]), reverse=False)
    
    # Nota: A ordenação por data_h_entrada para "mais recentes primeiro" 
    # exigiria reverse=True para a data, mas reverse=False para a prioridade.
    # Vou ajustar a lógica do key para permitir ordenação mista:
    fila.sort(key=lambda x: (ordem.get(x["prioridade"], 9), -x["data_h_entrada"].timestamp()))
    
    print(f"DEBUG: Fila para hospital '{id_hospital}' tem {len(fila)} pacientes.")
    
    return fila

@router.get("/episodes/{cod_epis}")
def obter_episodio_detalhado(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    # Join com Utilizador para obter o rececionista
    query = select(EpisodioUrgencia, Utilizador).join(
        Utilizador, EpisodioUrgencia.id_utilizador_rececao == Utilizador.id_utilizador, isouter=True
    ).where(EpisodioUrgencia.cod_epis == cod_epis)
    
    res = sessao.exec(query).first()
    if not res:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    
    episodio, rececionista = res
    utente = sessao.get(Utente, episodio.id_utente)
    
    # Triagem com nome do enfermeiro (LEFT JOIN)
    query_triagem = select(Triagem, Utilizador).join(
        Utilizador, or_(Triagem.num_func_enfermeiro == Utilizador.num_func, Triagem.num_func_enfermeiro == Utilizador.id_utilizador), isouter=True
    ).where(Triagem.cod_epis == cod_epis)
    res_triagem = sessao.exec(query_triagem).first()
    
    triagem_data = None
    if res_triagem:
        t, u = res_triagem
        triagem_data = t.dict()
        triagem_data["profissional_info"] = {
            "nome": u.nome_completo if u else f"Enfermeiro {t.num_func_enfermeiro}",
            "username": u.nome_utilizador if u else "---",
            "num_func": t.num_func_enfermeiro
        }

    return {
        "cod_epis": episodio.cod_epis,
        "data_h_entrada": episodio.data_h_entrada,
        "id_utente": episodio.id_utente,
        "id_hospital": episodio.id_hospital,
        "sintomas_iniciais": episodio.sintomas,
        "profissional_info": {
            "nome": rececionista.nome_completo if rececionista else "Utilizador Desconhecido",
            "username": rececionista.nome_utilizador if rececionista else "---",
            "num_func": rececionista.num_func if rececionista else (episodio.id_utilizador_rececao or "---")
        },
        "utente": utente,
        "triagem": triagem_data
    }

@router.get("/hospitals/{nome_hosp}/services", response_model=List[ServicoHospitalar])
def listar_servicos_hospital(nome_hosp: str, sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(ServicoHospitalar).where(ServicoHospitalar.id_hosp == nome_hosp)).all()

@router.get("/services/{id_servico}/available-beds")
def listar_camas_disponiveis(id_servico: int, sessao: Session = Depends(obter_sessao)):
    # Obter camas ocupadas para este serviço
    query_ocupadas = select(Internamento.num_cama).where(
        Internamento.id_servico == id_servico,
        Internamento.data_h_saida == None
    )
    camas_ocupadas = sessao.exec(query_ocupadas).all()
    
    # Cada especialidade tem 15 camas (1 a 15)
    todas_camas = list(range(1, 16))
    camas_livres = [c for c in todas_camas if c not in camas_ocupadas]
    
    return {"id_servico": id_servico, "camas_disponiveis": camas_livres}

@router.post("/internamentos", response_model=Internamento)
def criar_internamento(internamento: Internamento, sessao: Session = Depends(obter_sessao)):
    sessao.add(internamento)
    
    # Ao internar, o episódio de urgência termina
    episodio = sessao.get(EpisodioUrgencia, internamento.cod_epis)
    if episodio:
        episodio.data_h_saida = datetime.now(timezone.utc)
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
        data_h_triagem=datetime.now(timezone.utc)
    )
    
    sessao.add(db_triagem)
    sessao.commit()
    sessao.refresh(db_triagem)
    return db_triagem

@router.get("/utentes/{num_utente}/history")
def obter_historico_utente(num_utente: int, sessao: Session = Depends(obter_sessao), utilizador = Depends(obter_utilizador_atual)):
    # 0. Info do Utente
    db_utente = sessao.get(Utente, num_utente)
    utente_dict = db_utente.dict() if db_utente else None

    # 1. Episódios com Rececionista
    query = select(EpisodioUrgencia, Utilizador).join(
        Utilizador, EpisodioUrgencia.id_utilizador_rececao == Utilizador.id_utilizador, isouter=True
    ).where(EpisodioUrgencia.id_utente == num_utente).order_by(EpisodioUrgencia.data_h_entrada.desc())
    
    resultados_ep = sessao.exec(query).all()
    
    historico = []
    for ep, rececionista in resultados_ep:
        ep_dict = ep.dict()
        ep_dict["profissional_info"] = {
            "nome": rececionista.nome_completo if rececionista else f"Rececionista {ep.id_utilizador_rececao or '---'}",
            "username": rececionista.nome_utilizador if rececionista else "---",
            "num_func": rececionista.num_func if rececionista else "---"
        }
        # Campos de compatibilidade
        ep_dict["rececionista_nome"] = ep_dict["profissional_info"]["nome"]

        # Triagem
        query_triagem = select(Triagem, Utilizador).join(
            Utilizador, or_(Triagem.num_func_enfermeiro == Utilizador.num_func, Triagem.num_func_enfermeiro == Utilizador.id_utilizador), isouter=True
        ).where(Triagem.cod_epis == ep.cod_epis)
        res_triagem = sessao.exec(query_triagem).first()
        triagem_final = None
        if res_triagem:
            t, u = res_triagem
            triagem_final = t.dict()
            triagem_final["profissional_info"] = {
                "nome": u.nome_completo if u else f"Enfermeiro {t.num_func_enfermeiro}",
                "username": u.nome_utilizador if u else "---",
                "num_func": t.num_func_enfermeiro
            }
            # Campos de compatibilidade
            triagem_final["enfermeiro_nome"] = triagem_final["profissional_info"]["nome"]

        # Atos (Ordenados cronologicamente)
        query_atos = select(Ato, Utilizador).join(
            Utilizador, or_(Ato.num_func == Utilizador.num_func, Ato.num_func == Utilizador.id_utilizador), isouter=True
        ).where(Ato.cod_epis == ep.cod_epis).order_by(Ato.data_h_inicio.asc())
        res_atos = sessao.exec(query_atos).all()
        atos_finais = []
        for a, u in res_atos:
            ato_dict = a.dict()
            ato_dict["profissional_info"] = {
                "nome": u.nome_completo if u else f"Profissional {a.num_func}",
                "username": u.nome_utilizador if u else "---",
                "num_func": a.num_func
            }
            # Campos de compatibilidade
            ato_dict["profissional_nome"] = ato_dict["profissional_info"]["nome"]
            ato_dict["profissional_username"] = ato_dict["profissional_info"]["username"]
            atos_finais.append(ato_dict)

        # Prescrições (Ordenadas cronologicamente)
        query_presc = select(Prescricao, Utilizador).join(
            Utilizador, or_(Prescricao.num_func_medico == Utilizador.num_func, Prescricao.num_func_medico == Utilizador.id_utilizador), isouter=True
        ).where(Prescricao.cod_epis == ep.cod_epis).order_by(Prescricao.data_h_presc.asc())
        res_presc = sessao.exec(query_presc).all()
        presc_finais = []
        for p, u in res_presc:
            presc_dict = p.dict()
            presc_dict["profissional_info"] = {
                "nome": u.nome_completo if u else f"Médico {p.num_func_medico}",
                "username": u.nome_utilizador if u else "---",
                "num_func": p.num_func_medico
            }
            # Campos de compatibilidade
            presc_dict["medico_nome"] = presc_dict["profissional_info"]["nome"]
            presc_dict["medico_username"] = presc_dict["profissional_info"]["username"]
            presc_finais.append(presc_dict)

        # Internamento
        query_intern = select(Internamento, Utilizador).join(
            Utilizador, or_(Internamento.num_func_medico == Utilizador.num_func, Internamento.num_func_medico == Utilizador.id_utilizador), isouter=True
        ).where(Internamento.cod_epis == ep.cod_epis)
        res_intern = sessao.exec(query_intern).first()
        intern_final = None
        if res_intern:
            i, u = res_intern
            intern_final = i.dict()
            intern_final["profissional_info"] = {
                "nome": u.nome_completo if u else f"Médico {i.num_func_medico}",
                "username": u.nome_utilizador if u else "---",
                "num_func": i.num_func_medico
            }
            # Campos de compatibilidade
            intern_final["medico_nome"] = intern_final["profissional_info"]["nome"]
            intern_final["medico_username"] = intern_final["profissional_info"]["username"]
        
        historico.append({
            "episodio": ep_dict,
            "triagem": triagem_final,
            "atos": atos_finais,
            "prescricoes": presc_finais,
            "internamento": intern_final,
            "utente": utente_dict
        })
    
    return historico

@router.get("/episodes/{cod_epis}/prescriptions")
def listar_prescricoes_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    query = select(Prescricao, Utilizador).join(
        Utilizador, or_(Prescricao.num_func_medico == Utilizador.num_func, Prescricao.num_func_medico == Utilizador.id_utilizador), isouter=True
    ).where(Prescricao.cod_epis == cod_epis)
    
    resultados = sessao.exec(query).all()
    
    presc_finais = []
    for p, u in resultados:
        p_dict = p.dict()
        p_dict["medico_nome"] = u.nome_completo if u else f"Dr. {p.num_func_medico}"
        p_dict["medico_username"] = u.nome_utilizador if u else "---"
        presc_finais.append(p_dict)
        
    return presc_finais

# ATOS
@router.post("/atos", response_model=Ato)
def criar_ato(ato: Ato, sessao: Session = Depends(obter_sessao)):
    sessao.add(ato)
    sessao.flush() # Importante para obter id_ato
    
    # Registar na tabela original ENVOLVE
    db_envolve = Envolve(
        id_ato=ato.id_ato,
        num_func=ato.num_func,
        data_h_inicio=ato.data_h_inicio,
        cod_epis=ato.cod_epis,
        id_hosp=ato.id_hosp
    )
    sessao.add(db_envolve)
    
    # Se a decisão clínica for ALTA, fechar o episódio
    if ato.decisao_clinica == "ALTA":
        episodio = sessao.get(EpisodioUrgencia, ato.cod_epis)
        if episodio:
            episodio.data_h_saida = datetime.now(timezone.utc)
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
            u_medico = sessao.exec(select(Utilizador).where(or_(Utilizador.num_func == intern.num_func_medico, Utilizador.id_utilizador == intern.num_func_medico))).first()
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
    
    agora = datetime.now(timezone.utc)
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
    episodio.data_h_saida = datetime.now(timezone.utc)
    sessao.add(episodio)
    sessao.commit()
    return {"message": "Paciente teve alta"}
