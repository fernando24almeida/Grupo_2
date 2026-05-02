from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select, func, union_all
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, date
from ..core.db import obter_sessao
from ..models.models import Utente, EpisodioUrgencia, Triagem, Ato, Prescricao, Internamento, Hospital, Envolve, FuncionarioHospital
from ..core.security import RoleChecker
from ..core.audit import log_audit

router = APIRouter()
admin_only = RoleChecker(["ADMIN"])

# SCHEMAS
class CriarEpisodio(BaseModel):
    id_utente: int
    id_hospital: str
    data_h_entrada: Optional[datetime] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None

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

class AtualizarHospital(BaseModel):
    local_hosp: Optional[str] = None

class AtualizarEpisodio(BaseModel):
    data_h_entrada: Optional[datetime] = None
    data_h_saida: Optional[datetime] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None

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

import random
import string
from ..core.security import obter_hash_palavra_passe, verificar_palavra_passe, criar_token_acesso, obter_utilizador_atual
from ..core.email import enviar_email_ativacao
from ..models.models import EmailValidation

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
    existente_email = sessao.exec(select(Utente).where(Utente.email == dados.email.lower().strip())).first()
    if existente_email:
        raise HTTPException(status_code=400, detail=f"O e-mail {dados.email} já está associado a outro utente.")

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
    
    # 4. Gerar PIN temporário
    pin_temporario = ''.join(random.choices(string.digits, k=6))
    
    # 5. Criar objeto Utente
    novo_utente = Utente(
        num_utente=dados.num_utente,
        nome=dados.nome,
        email=dados.email.lower().strip(),
        telemovel=dados.telemovel or None,
        morada=dados.morada or None,
        localidade=dados.localidade or None,
        sexo=dados.sexo or "M",
        data_nascimento=data_nasc,
        password_hash=obter_hash_palavra_passe(pin_temporario),
        ativo=False,
        primeiro_acesso=True
    )
    
    # 6. Gerar código de ativação
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
        return {
            "success": True,
            "message": "Utente registado com sucesso! Verifique o seu e-mail para ativar a conta.",
            "data": novo_utente
        }
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
    
    return {"message": "PIN alterado com sucesso. Já pode aceder à App."}

@router.get("/utentes", response_model=List[Utente])
def ler_utentes(sessao: Session = Depends(obter_sessao)):
    utentes = sessao.exec(select(Utente)).all()
    return utentes

@router.post("/utentes/{num_utente}/resend-activation", dependencies=[Depends(admin_only)])
async def reenviar_ativacao_utente(num_utente: int, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(obter_utilizador_atual)):
    utente = sessao.get(Utente, num_utente)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    
    if utente.ativo:
        raise HTTPException(status_code=400, detail="Este utente já tem a conta ativa.")

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
        
        log_audit(sessao, admin.id_utilizador, "RESEND_ACTIVATION", "utente", str(num_utente), f"Novo PIN e código enviados para {utente.email}")
        
        print(f"\n📧 [DEBUG REENVIO] Utente {utente.num_utente} | Novo PIN: {pin_temporario} | Novo Código: {codigo_ativacao}\n")
        
        return {"message": "Novo PIN e código de ativação enviados com sucesso."}
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

@router.patch("/utentes/{num_utente}", response_model=Utente, dependencies=[Depends(admin_only)])
def atualizar_utente(num_utente: int, utente_in: AtualizarUtente, sessao: Session = Depends(obter_sessao)):
    db_utente = sessao.get(Utente, num_utente)
    if not db_utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    dados = utente_in.dict(exclude_unset=True)
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

# EPISODIOS
@router.post("/episodes", response_model=EpisodioUrgencia)
def criar_episodio(dados_epis: CriarEpisodio, sessao: Session = Depends(obter_sessao)):
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
        observacoes=dados_epis.observacoes
    )
    
    sessao.add(db_episodio)
    sessao.commit()
    sessao.refresh(db_episodio)
    return db_episodio

@router.get("/episodes", response_model=List[EpisodioUrgencia])
def ler_episodios(
    id_hospital: Optional[str] = None, 
    sessao: Session = Depends(obter_sessao)
):
    query = select(EpisodioUrgencia)
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    
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
    # Lógica baseada nas tabelas ORIGINAIS:
    # 1. Buscar enfermeiro da Triagem
    # 2. Buscar médicos de Atos/Envolve
    # 3. Buscar médicos de Prescrições
    
    equipa = []
    
    # Triagem
    triagem = sessao.exec(select(Triagem, FuncionarioHospital).join(FuncionarioHospital, Triagem.num_func_enfermeiro == FuncionarioHospital.num_func).where(Triagem.cod_epis == cod_epis)).all()
    for t, f in triagem:
        equipa.append({"num_func": f.num_func, "tipo_func": f.tipo_func, "papel": "Triagem", "data": t.data_h_triagem})
        
    # Atos (via Envolve)
    envolvimentos = sessao.exec(select(Envolve, FuncionarioHospital).join(FuncionarioHospital, Envolve.num_func == FuncionarioHospital.num_func).where(Envolve.cod_epis == cod_epis)).all()
    for e, f in envolvimentos:
        equipa.append({"num_func": f.num_func, "tipo_func": f.tipo_func, "papel": "Ato Clínico", "data": e.data_h_inicio})
        
    # Prescrições
    prescricoes = sessao.exec(select(Prescricao, FuncionarioHospital).join(FuncionarioHospital, Prescricao.num_func_medico == FuncionarioHospital.num_func).where(Prescricao.cod_epis == cod_epis)).all()
    for p, f in prescricoes:
        equipa.append({"num_func": f.num_func, "tipo_func": f.tipo_func, "papel": "Prescrição", "data": p.data_h_presc})
        
    return equipa

@router.get("/episodes/awaiting-triage", response_model=List[EpisodioUrgencia])
def ler_episodios_aguardando_triagem(
    id_hospital: Optional[str] = None, 
    sessao: Session = Depends(obter_sessao)
):
    # Selecionar episódios que não têm triagem e não têm data de saída
    query = select(EpisodioUrgencia).where(
        EpisodioUrgencia.data_h_saida == None,
        ~EpisodioUrgencia.cod_epis.in_(select(Triagem.cod_epis))
    )
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    
    # Ordem de chegada (mais antigos primeiro)
    query = query.order_by(EpisodioUrgencia.data_h_entrada.asc())
    
    return sessao.exec(query).all()

# TRIAGEM
@router.post("/triagens", response_model=Triagem)
def criar_triagem(triagem: Triagem, sessao: Session = Depends(obter_sessao)):
    sessao.add(triagem)
    sessao.commit()
    sessao.refresh(triagem)
    return triagem

@router.get("/episodes/{cod_epis}")
def obter_episodio_detalhado(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    utente = sessao.get(Utente, episodio.id_utente)
    # Procurar a triagem deste episódio
    triagem = sessao.exec(select(Triagem).where(Triagem.cod_epis == cod_epis)).first()
    
    return {
        "cod_epis": episodio.cod_epis,
        "data_h_entrada": episodio.data_h_entrada,
        "id_utente": episodio.id_utente,
        "id_hospital": episodio.id_hospital,
        "sintomas_iniciais": episodio.sintomas,
        "utente": utente,
        "triagem": triagem
    }

@router.get("/episodes/awaiting-doctor", response_model=List[dict])
def ler_episodios_aguardando_medico(
    id_hospital: Optional[str] = None, 
    sessao: Session = Depends(obter_sessao)
):
    # Selecionar episódios que TÊM triagem e NÃO têm data de saída
    query = select(EpisodioUrgencia, Triagem, Utente).join(
        Triagem, EpisodioUrgencia.cod_epis == Triagem.cod_epis
    ).join(
        Utente, EpisodioUrgencia.id_utente == Utente.num_utente
    ).where(
        EpisodioUrgencia.data_h_saida == None
    )
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    
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
    
    return fila

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
def obter_historico_utente(num_utente: int, sessao: Session = Depends(obter_sessao)):
    # 1. Obter todos os episódios do utente
    episodios = sessao.exec(
        select(EpisodioUrgencia).where(EpisodioUrgencia.id_utente == num_utente).order_by(EpisodioUrgencia.data_h_entrada.desc())
    ).all()
    
    historico = []
    for ep in episodios:
        # Para cada episódio, buscar a triagem e atos
        triagem = sessao.exec(select(Triagem).where(Triagem.cod_epis == ep.cod_epis)).first()
        atos = sessao.exec(select(Ato).where(Ato.cod_epis == ep.cod_epis)).all()
        prescricoes = sessao.exec(select(Prescricao).where(Prescricao.cod_epis == ep.cod_epis)).all()
        
        historico.append({
            "episodio": ep,
            "triagem": triagem,
            "atos": atos,
            "prescricoes": prescricoes
        })
    
    resumo_historico = []
    for item in historico:
        ep = item["episodio"]
        tri = item["triagem"]
        resumo_historico.append({
            "id": str(ep.cod_epis),
            "data": ep.data_h_entrada.strftime("%Y-%m-%d %H:%M"),
            "hospital": ep.id_hospital,
            "estado": "Concluído" if ep.data_h_saida else "Em curso",
            "prioridade": tri.prioridade if tri else "N/A"
        })
    return {
        "success": True,
        "message": "Histórico obtido com sucesso",
        "data": resumo_historico
    }

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
    
    sessao.commit()
    sessao.refresh(ato)
    return ato

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
