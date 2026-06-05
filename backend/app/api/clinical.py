from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlmodel import Session, select, func, or_
from pydantic import BaseModel, field_validator
from typing import List, Optional, Any
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

# --- SCHEMAS PARA API MOBILE ---

class LoginRequestMobile(BaseModel):
    num_utente: str
    pin: str

class RegisterRequestMobile(BaseModel):
    num_utente: str
    nome: str
    pin: str
    email: str

class UtenteCriar(BaseModel):
    num_utente: int
    nome: str
    email: str
    telemovel: Optional[str] = None
    morada: Optional[str] = None
    localidade: Optional[str] = None
    sexo: Optional[str] = "M"
    data_nascimento: Optional[date] = None
    parentesco: Optional[str] = None
    pin: Optional[str] = None

    @field_validator('data_nascimento', mode='before')
    @classmethod
    def validar_data_vazia(cls, v):
        if v == "":
            return None
        return v

    @field_validator('telemovel', 'morada', 'localidade', 'parentesco', mode='before')
    @classmethod
    def string_vazia_para_none(cls, v):
        if v == "":
            return None
        return v

class ApiResponseMobile(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None

# =============================================================================
# ROTAS DE GESTÃO CLÍNICA (O CORAÇÃO DO SISTEMA)
# ... (rest of the file)

# =============================================================================
# ROTAS DE GESTÃO CLÍNICA (O CORAÇÃO DO SISTEMA)
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro gere toda a jornada do paciente: desde que entra no hospital 
# (Admissão), passa pela Triagem (Manchester), é visto pelo Médico (Atos) 
# e recebe alta ou fica internado. É aqui que os dados fluem entre equipas.
# =============================================================================

router = APIRouter()
admin_only = RoleChecker(["ADMIN"])

# --- SCHEMAS DE ENTRADA (MOLDES) ---
# Definimos o que o Frontend tem de enviar para cada ação.

class CriarEpisodio(BaseModel):
    id_utente: int
    id_hospital: str
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None

class CriarTriagem(BaseModel):
    cod_epis: str
    prioridade: str
    tensao_arterial: str
    temperatura: float
    sintomas: str
    observacoes: Optional[str] = None
    num_func_enfermeiro: int

# --- FUNCIONALIDADES DE EPISÓDIOS ---

@router.get("/episodes")
def listar_episodios(id_hospital: Optional[str] = None, em_aberto: Optional[bool] = None, sessao: Session = Depends(obter_sessao)):
    """ 
    Lista todos os episódios de urgência. 
    Permite filtrar por hospital e ver quem ainda está na urgência (em aberto).
    """
    query = select(EpisodioUrgencia)
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    if em_aberto:
        query = query.where(EpisodioUrgencia.data_h_saida == None)
    
    return sessao.exec(query.order_by(EpisodioUrgencia.data_h_entrada.desc())).all()

@router.post("/episodes", response_model=EpisodioUrgencia)
def criar_episodio(dados: CriarEpisodio, sessao: Session = Depends(obter_sessao), utilizador: Utilizador = Depends(obter_utilizador_atual)):
    """ 
    Admissão: Cria um novo código de episódio para o utente que acabou de chegar.
    Verifica primeiro se o utente já tem um episódio em aberto.
    """
    # VERIFICAÇÃO DE INTEGRIDADE: Impedir múltiplos episódios abertos
    existente = sessao.exec(select(EpisodioUrgencia).where(
        EpisodioUrgencia.id_utente == dados.id_utente,
        EpisodioUrgencia.data_h_saida == None
    )).first()
    
    if existente:
        raise HTTPException(
            status_code=400, 
            detail=f"O utente {dados.id_utente} já tem um episódio de urgência em aberto ({existente.cod_epis})."
        )

    agora = datetime.now(timezone.utc)
    novo_cod = f"EP{agora.year}{agora.month:02d}{random.randint(1000, 9999)}"
    
    db_episodio = EpisodioUrgencia(
        cod_epis=novo_cod,
        data_h_entrada=agora,
        id_utente=dados.id_utente,
        id_hospital=dados.id_hospital,
        sintomas=dados.sintomas,
        observacoes=dados.observacoes,
        id_utilizador_rececao=utilizador.id_utilizador
    )
    sessao.add(db_episodio)
    sessao.commit()
    sessao.refresh(db_episodio)
    return db_episodio

@router.get("/episodes/awaiting-triage")
def episodios_aguardando_triagem(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    """ Filtra os doentes que entraram mas ainda não foram vistos pelo enfermeiro. """
    query = select(EpisodioUrgencia).where(
        EpisodioUrgencia.data_h_saida == None,
        ~EpisodioUrgencia.cod_epis.in_(select(Triagem.cod_epis))
    )
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    return sessao.exec(query).all()

@router.get("/episodes/awaiting-doctor")
def episodios_aguardando_medico(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    """ 
    Fila de espera do Médico: Ordenada pela cor da Triagem (Vermelho primeiro!).
    Exclui pacientes que já foram movidos para internamento.
    """
    # Subquery para encontrar episódios que já têm internamento ativo
    internados = select(Internamento.cod_epis).where(Internamento.data_h_saida == None)
    
    query = select(EpisodioUrgencia, Triagem, Utente).join(Triagem).join(Utente).where(
        EpisodioUrgencia.data_h_saida == None,
        ~EpisodioUrgencia.cod_epis.in_(internados)
    )
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    
    resultados = sessao.exec(query).all()
    fila = []
    for ep, tri, ut in resultados:
        fila.append({
            "cod_epis": ep.cod_epis,
            "utente_nome": ut.nome,
            "prioridade": tri.prioridade,
            "data_h_entrada": ep.data_h_entrada
        })
    
    # Ordenação por gravidade (Manchester)
    ordem = {"VERMELHO": 0, "LARANJA": 1, "AMARELO": 2, "VERDE": 3, "AZUL": 4}
    fila.sort(key=lambda x: (ordem.get(x["prioridade"], 9), x["data_h_entrada"]))
    return fila

# --- FUNCIONALIDADES DE UTENTES ---

@router.post("/utentes/login")
def login_utente_mobile(dados: LoginRequestMobile, sessao: Session = Depends(obter_sessao)):
    """ Endpoint de login específico para a App Mobile. """
    try:
        utente = sessao.get(Utente, int(dados.num_utente))
        if utente and verificar_palavra_passe(dados.pin, utente.password_hash):
            token = criar_token_acesso(dados={"sub": str(utente.num_utente), "role": "UTENTE"})
            return {
                "success": True,
                "message": "Login com sucesso",
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
    except Exception:
        pass
        
    return {
        "success": False,
        "message": "NIF ou PIN incorretos",
        "data": None
    }

@router.post("/utentes")
async def registar_utente(dados: UtenteCriar, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    """ Endpoint de registo de utentes. Suporta criação via Staff e Mobile. """
    try:
        num_utente = int(dados.num_utente)
        existente = sessao.get(Utente, num_utente)
        if existente:
            return {
                "success": False,
                "message": "Utente já registado com este NIF",
                "data": None
            }
        
        # Gerar PIN se não fornecido
        pin_final = dados.pin
        if not pin_final:
            pin_final = ''.join(random.choices(string.digits, k=6))
            
        novo = Utente(
            num_utente=num_utente,
            nome=dados.nome,
            email=dados.email,
            telemovel=dados.telemovel,
            morada=dados.morada,
            localidade=dados.localidade,
            sexo=dados.sexo,
            data_nascimento=dados.data_nascimento,
            parentesco=dados.parentesco,
            password_hash=obter_hash_palavra_passe(pin_final),
            ativo=True,
            primeiro_acesso=False,
            id_role=5 # Papel UTENTE
        )
        sessao.add(novo)
        sessao.commit()
        sessao.refresh(novo)
        
        # Enviar e-mail de ativação com o PIN
        background_tasks.add_task(enviar_email_ativacao, novo.email, novo.nome, pin_final)
        
        return {
            "success": True,
            "message": "Conta criada com sucesso. PIN enviado por e-mail.",
            "data": novo
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao criar conta: {str(e)}",
            "data": None
        }

@router.get("/utentes/me", response_model=Utente)
def obter_meu_perfil_utente(utente_atual: Utente = Depends(obter_utilizador_atual)):
    """ Devolve os dados do utente que está logado na App Mobile. """
    return utente_atual

class AtualizarUtente(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telemovel: Optional[str] = None
    morada: Optional[str] = None
    localidade: Optional[str] = None
    password: Optional[str] = None
    ativo: Optional[bool] = None

@router.patch("/utentes/me", response_model=Utente)
def atualizar_meu_perfil_utente(dados: AtualizarUtente, sessao: Session = Depends(obter_sessao), utente_atual: Utente = Depends(obter_utilizador_atual)):
    """ Permite ao utente atualizar os seus dados de contacto e PIN. """
    update_data = dados.dict(exclude_unset=True)
    
    if "password" in update_data:
        password = update_data.pop("password")
        utente_atual.password_hash = obter_hash_palavra_passe(password)
        
    for chave, valor in update_data.items():
        setattr(utente_atual, chave, valor)
    
    sessao.add(utente_atual)
    sessao.commit()
    sessao.refresh(utente_atual)
    return utente_atual

@router.patch("/utentes/{num_utente}", response_model=Utente)
def atualizar_utente_admin(num_utente: int, dados: AtualizarUtente, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(admin_only)):
    """ Permite ao administrador atualizar qualquer dado de um utente. """
    utente = sessao.get(Utente, num_utente)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    
    update_data = dados.dict(exclude_unset=True)
    
    if "password" in update_data:
        password = update_data.pop("password")
        if password: # Só altera se não for vazio
            utente.password_hash = obter_hash_palavra_passe(password)
        
    for chave, valor in update_data.items():
        setattr(utente, chave, valor)
    
    sessao.add(utente)
    sessao.commit()
    sessao.refresh(utente)
    return utente

@router.get("/utentes")
def listar_utentes(sessao: Session = Depends(obter_sessao)):
    """ Lista todos os pacientes registados. """
    return sessao.exec(select(Utente)).all()

@router.get("/utentes/search")
def pesquisar_utente(num_utente: Optional[int] = None, nome: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    """ Permite ao rececionista encontrar um doente pelo NIF ou Nome. """
    query = select(Utente)
    if num_utente:
        query = query.where(Utente.num_utente == num_utente)
    if nome:
        query = query.where(func.lower(Utente.nome).like(f"%{nome.lower()}%"))
    return sessao.exec(query.limit(10)).all()

@router.delete("/utentes/{num_utente}")
def eliminar_utente(num_utente: int, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(admin_only)):
    """ 
    Remoção Lógica de Utente: Inativa o utente e anonimiza dados sensíveis.
    Não apaga o registo para manter a integridade do histórico clínico.
    """
    utente = sessao.get(Utente, num_utente)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    
    # Verificar se tem episódios abertos
    tem_abertos = sessao.exec(select(EpisodioUrgencia).where(
        EpisodioUrgencia.id_utente == num_utente,
        EpisodioUrgencia.data_h_saida == None
    )).first()
    
    if tem_abertos:
        raise HTTPException(
            status_code=400, 
            detail="Não é possível remover um utente com episódios de urgência em aberto."
        )

    # Anonimização e Inativação
    utente.ativo = False
    utente.email = f"anonimo_{num_utente}@clinica.g2"
    utente.telemovel = "900000000"
    utente.morada = "REMOVIDO"
    utente.password_hash = "INATIVO" # Bloqueia acesso à App Mobile
    
    sessao.add(utente)
    sessao.commit()
    return {"message": "Utente removido logicamente e dados anonimizados"}

@router.post("/utentes/{num_utente}/toggle-status", dependencies=[Depends(admin_only)])
def alternar_estado_utente(num_utente: int, sessao: Session = Depends(obter_sessao)):
    utente = sessao.get(Utente, num_utente)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    utente.ativo = not utente.ativo
    sessao.add(utente)
    sessao.commit()
    return {"message": f"Estado alterado para {'Ativo' if utente.ativo else 'Inativo'}"}

@router.post("/utentes/{num_utente}/resend-activation", dependencies=[Depends(admin_only)])
def reenviar_ativacao_utente(num_utente: int, background_tasks: BackgroundTasks, sessao: Session = Depends(obter_sessao)):
    utente = sessao.get(Utente, num_utente)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente não encontrado")
    
    # Para utentes, enviamos o PIN de 6 dígitos que eles usam na App Mobile
    # Se não tiver password_hash, geramos um novo PIN.
    # Mas o mais comum aqui é apenas reenviar o e-mail de boas-vindas com um PIN novo
    novo_pin = ''.join(random.choices(string.digits, k=6))
    utente.password_hash = obter_hash_palavra_passe(novo_pin)
    sessao.add(utente)
    sessao.commit()
    
    background_tasks.add_task(enviar_email_ativacao, utente.email, utente.nome, novo_pin)
    return {"message": "Novo PIN de ativação enviado por e-mail"}

# --- HISTÓRICO E JORNADA ---

@router.get("/utentes/{num_utente}/history")
def obter_historico_utente(num_utente: int, sessao: Session = Depends(obter_sessao)):
    """ 
    Reúne tudo: Episódios, Triagens, Atos e Receitas do utente. 
    É a visão 360º para o médico. Inclui agora também dados de internamento.
    """
    episodios = sessao.exec(select(EpisodioUrgencia).where(EpisodioUrgencia.id_utente == num_utente).order_by(EpisodioUrgencia.data_h_entrada.desc())).all()
    historico = []
    for ep in episodios:
        # 1. Triagem com info do enfermeiro
        res_tri = sessao.exec(select(Triagem, Utilizador).join(
            Utilizador, Triagem.num_func_enfermeiro == Utilizador.num_func, isouter=True
        ).where(Triagem.cod_epis == ep.cod_epis)).first()
        
        triagem_data = None
        if res_tri:
            tri, enf = res_tri
            triagem_data = tri.dict()
            triagem_data["profissional_info"] = {"nome": enf.nome_completo} if enf else {"nome": "Desconhecido"}

        # 2. Atos com info do médico
        res_atos = sessao.exec(select(Ato, Utilizador).join(
            Utilizador, Ato.num_func == Utilizador.num_func, isouter=True
        ).where(Ato.cod_epis == ep.cod_epis)).all()
        
        atos_data = []
        for a, u in res_atos:
            a_dict = a.dict()
            a_dict["profissional_nome"] = u.nome_completo if u else "Desconhecido"
            atos_data.append(a_dict)

        # 3. Prescrições com info do médico
        res_presc = sessao.exec(select(Prescricao, Utilizador).join(
            Utilizador, Prescricao.num_func_medico == Utilizador.num_func, isouter=True
        ).where(Prescricao.cod_epis == ep.cod_epis)).all()
        
        presc_data = []
        for p, u in res_presc:
            p_dict = p.dict()
            p_dict["medico_nome"] = u.nome_completo if u else "Desconhecido"
            presc_data.append(p_dict)

        # 4. Internamento com info do médico responsável
        res_int = sessao.exec(select(Internamento, Utilizador).join(
            Utilizador, Internamento.num_func_medico == Utilizador.num_func, isouter=True
        ).where(Internamento.cod_epis == ep.cod_epis)).first()
        
        intern_data = None
        if res_int:
            i, m = res_int
            intern_data = i.dict()
            intern_data["medico_nome"] = m.nome_completo if m else "Não atribuído"
            intern_data["medico_username"] = m.nome_utilizador if m else "N/A"
            intern_data["profissional_info"] = {
                "nome": m.nome_completo if m else "Não atribuído",
                "username": m.nome_utilizador if m else "N/A",
                "num_func": m.num_func if m else None
            }

        historico.append({
            "episodio": ep,
            "triagem": triagem_data,
            "atos": atos_data,
            "prescricoes": presc_data,
            "internamento": intern_data
        })
    return historico

@router.get("/utentes/{num_utente}/history/mobile")
def obter_historico_utente_mobile(num_utente: int, sessao: Session = Depends(obter_sessao)):
    """ Versão do histórico compatível com a App Mobile (com wrapper ApiResponse). """
    historico = obter_historico_utente(num_utente, sessao)
    return {
        "success": True,
        "message": "Histórico carregado",
        "data": historico
    }

# --- INFRAESTRUTURA ---

@router.get("/episodes/{cod_epis}/journey")
def obter_percurso_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    """ 
    Endpoint agregador para mostrar toda a 'viagem' do doente num episódio:
    Admissão -> Triagem -> Atos -> Prescrições -> Internamento -> Alta.
    """
    # 1. Obter Episódio base
    episodio = sessao.exec(select(EpisodioUrgencia).where(EpisodioUrgencia.cod_epis == cod_epis)).first()
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    
    # Adicionar info de quem fez a receção
    res_rececao = sessao.exec(select(Utilizador).where(Utilizador.id_utilizador == episodio.id_utilizador_rececao)).first()
    ep_data = episodio.dict()
    ep_data["profissional_info"] = {
        "nome": res_rececao.nome_completo,
        "username": res_rececao.nome_utilizador,
        "num_func": res_rececao.num_func
    } if res_rececao else {"nome": "Sistema", "username": "admin", "num_func": 1}

    # 2. Obter Utente
    utente = sessao.get(Utente, episodio.id_utente)
    
    # 3. Obter Triagem
    res_tri = sessao.exec(select(Triagem, Utilizador).join(
        Utilizador, Triagem.num_func_enfermeiro == Utilizador.num_func, isouter=True
    ).where(Triagem.cod_epis == cod_epis)).first()
    
    triagem_data = None
    if res_tri:
        tri, enf = res_tri
        triagem_data = tri.dict()
        triagem_data["profissional_info"] = {
            "nome": enf.nome_completo,
            "username": enf.nome_utilizador,
            "num_func": enf.num_func
        } if enf else {"nome": "Desconhecido"}

    # 4. Obter Atos
    res_atos = sessao.exec(select(Ato, Utilizador).join(
        Utilizador, Ato.num_func == Utilizador.num_func, isouter=True
    ).where(Ato.cod_epis == cod_epis)).all()
    
    atos_data = []
    for a, u in res_atos:
        a_dict = a.dict()
        a_dict["profissional_info"] = {
            "nome": u.nome_completo,
            "username": u.nome_utilizador,
            "num_func": u.num_func
        } if u else {"nome": "Desconhecido"}
        atos_data.append(a_dict)

    # 5. Obter Prescrições
    res_presc = sessao.exec(select(Prescricao, Utilizador).join(
        Utilizador, Prescricao.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Prescricao.cod_epis == cod_epis)).all()
    
    presc_data = []
    for p, u in res_presc:
        p_dict = p.dict()
        p_dict["profissional_info"] = {
            "nome": u.nome_completo,
            "username": u.nome_utilizador,
            "num_func": u.num_func
        } if u else {"nome": "Desconhecido"}
        presc_data.append(p_dict)

    # 6. Obter Internamento
    res_int = sessao.exec(select(Internamento, Utilizador).join(
        Utilizador, Internamento.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Internamento.cod_epis == cod_epis)).first()
    
    intern_data = None
    if res_int:
        i, m = res_int
        intern_data = i.dict()
        intern_data["profissional_info"] = {
            "nome": m.nome_completo,
            "username": m.nome_utilizador,
            "num_func": m.num_func
        } if m else {"nome": "Não atribuído"}

    return {
        "episodio": ep_data,
        "utente": utente,
        "triagem": triagem_data,
        "atos": atos_data,
        "prescricoes": presc_data,
        "internamento": intern_data
    }

@router.get("/hospitals")
def ler_hospitais(sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(Hospital)).all()

@router.delete("/hospitals/{nome_hosp}")
def eliminar_hospital(nome_hosp: str, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(admin_only)):
    """ Remove um hospital se não tiver episódios associados. """
    hospital = sessao.get(Hospital, nome_hosp)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    
    # Impedir eliminação se houver dados dependentes
    tem_episodios = sessao.exec(select(EpisodioUrgencia).where(EpisodioUrgencia.id_hospital == nome_hosp)).first()
    if tem_episodios:
        raise HTTPException(status_code=400, detail="Não é possível eliminar um hospital com episódios registados.")
        
    sessao.delete(hospital)
    sessao.commit()
    return {"message": "Hospital eliminado com sucesso"}

@router.get("/internamentos")
def listar_internamentos(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    """ Mostra quem está atualmente internado nas enfermarias. """
    query = select(Internamento, Utente, ServicoHospitalar, Utilizador).join(
        EpisodioUrgencia, Internamento.cod_epis == EpisodioUrgencia.cod_epis
    ).join(
        Utente, EpisodioUrgencia.id_utente == Utente.num_utente
    ).join(
        ServicoHospitalar, Internamento.id_servico == ServicoHospitalar.id_servico
    ).join(
        Utilizador, Internamento.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Internamento.data_h_saida == None)
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
    
    res = sessao.exec(query).all()
    
    return [
        {
            "num_internamento": i.num_internamento,
            "cod_epis": i.cod_epis,
            "utente_nome": u.nome,
            "num_cama": i.num_cama,
            "servico_nome": s.nome,
            "data_h_entrada": i.data_h_entrada,
            "medico_responsavel": m.nome_completo if m else "Não atribuído"
        } 
        for i, u, s, m in res
    ]

# --- NOVOS ENDPOINTS PARA COMPLETAR O FLUXO ---

@router.get("/episodes/{cod_epis}")
def obter_detalhe_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    """ Retorna todos os dados de um episódio específico. """
    episodio = sessao.exec(select(EpisodioUrgencia).where(EpisodioUrgencia.cod_epis == cod_epis)).first()
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    
    utente = sessao.get(Utente, episodio.id_utente)
    triagem = sessao.exec(select(Triagem).where(Triagem.cod_epis == cod_epis)).first()
    internamento = sessao.exec(select(Internamento).where(Internamento.cod_epis == cod_epis, Internamento.data_h_saida == None)).first()
    
    res = episodio.dict()
    res["utente"] = utente
    res["triagem"] = triagem
    res["utente_nome"] = utente.nome if utente else "Desconhecido"
    res["prioridade"] = triagem.prioridade if triagem else "PENDENTE"
    
    if internamento:
        servico = sessao.get(ServicoHospitalar, internamento.id_servico)
        res["internamento"] = {
            "num_internamento": internamento.num_internamento,
            "servico_nome": servico.nome if servico else "Desconhecido",
            "num_cama": internamento.num_cama,
            "data_h_entrada": internamento.data_h_entrada
        }
    
    return res

@router.delete("/episodes/{cod_epis}")
def eliminar_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao), admin: Utilizador = Depends(admin_only)):
    """ 
    Remove um episódio e todos os registos associados (Triagem, Atos, etc.).
    Apenas disponível para administradores.
    """
    episodio = sessao.get(EpisodioUrgencia, cod_epis)
    if not episodio:
        raise HTTPException(status_code=404, detail="Episódio não encontrado")
    
    # 1. Triagens
    triagens = sessao.exec(select(Triagem).where(Triagem.cod_epis == cod_epis)).all()
    for t in triagens:
        sessao.delete(t)
        
    # 2. Atos
    atos = sessao.exec(select(Ato).where(Ato.cod_epis == cod_epis)).all()
    for a in atos:
        # Envolve relations
        envolvidos = sessao.exec(select(Envolve).where(Envolve.id_ato == a.id_ato)).all()
        for env in envolvidos:
            sessao.delete(env)
        sessao.delete(a)
        
    # 3. Prescrições
    prescricoes = sessao.exec(select(Prescricao).where(Prescricao.cod_epis == cod_epis)).all()
    for p in prescricoes:
        sessao.delete(p)
        
    # 4. Internamentos
    internamentos = sessao.exec(select(Internamento).where(Internamento.cod_epis == cod_epis)).all()
    for i in internamentos:
        sessao.delete(i)
        
    # 5. O Episódio
    sessao.delete(episodio)
    
    sessao.commit()
    return {"message": "Episódio e dados relacionados eliminados com sucesso"}

@router.get("/episodes/{cod_epis}/prescriptions")
def listar_prescricoes_episodio(cod_epis: str, sessao: Session = Depends(obter_sessao)):
    query = select(Prescricao, Utilizador).join(
        Utilizador, Prescricao.num_func_medico == Utilizador.num_func, isouter=True
    ).where(Prescricao.cod_epis == cod_epis)
    
    res = sessao.exec(query).all()
    return [
        {
            "num_prescricao": p.num_prescricao,
            "medicamento": p.medicamento,
            "dosagem": p.dosagem,
            "data_h_presc": p.data_h_presc,
            "medico_nome": u.nome_completo if u else "Desconhecido"
        }
        for p, u in res
    ]

@router.get("/hospitals/{id_hosp}/services")
def listar_servicos_hospital(id_hosp: str, sessao: Session = Depends(obter_sessao)):
    return sessao.exec(select(ServicoHospitalar).where(ServicoHospitalar.id_hosp == id_hosp)).all()

@router.get("/services/{id_servico}/available-beds")
def listar_camas_disponiveis(id_servico: int, sessao: Session = Depends(obter_sessao)):
    """ 
    Lógica simplificada: Assume que cada serviço tem 15 camas 
    e subtrai as que estão ocupadas.
    """
    total_camas = 15
    ocupadas = sessao.exec(select(Internamento.num_cama).where(
        Internamento.id_servico == id_servico,
        Internamento.data_h_saida == None
    )).all()
    
    camas_ocupadas = set(ocupadas)
    disponiveis = [c for c in range(1, total_camas + 1) if c not in camas_ocupadas]
    
    return {"id_servico": id_servico, "camas_disponiveis": disponiveis}

@router.post("/internamentos")
def criar_internamento(dados: dict, sessao: Session = Depends(obter_sessao)):
    novo = Internamento(
        cod_epis=dados["cod_epis"],
        id_servico=dados["id_servico"],
        num_cama=dados.get("num_cama"),
        num_func_medico=dados.get("num_func_medico")
    )
    sessao.add(novo)
    sessao.commit()
    sessao.refresh(novo)
    return novo

@router.post("/internamentos/{id_int}/discharge")
def dar_alta_internamento(id_int: int, sessao: Session = Depends(obter_sessao)):
    intern = sessao.get(Internamento, id_int)
    if not intern:
        raise HTTPException(status_code=404, detail="Internamento não encontrado")
    
    intern.data_h_saida = datetime.now(timezone.utc)
    sessao.add(intern)
    
    # Fechar também o episódio de urgência
    episodio = sessao.get(EpisodioUrgencia, intern.cod_epis)
    if episodio:
        episodio.data_h_saida = intern.data_h_saida
        sessao.add(episodio)
    
    sessao.commit()
    return {"message": "Alta registada com sucesso"}

@router.post("/triagens/manchester")
def registar_triagem_manchester(dados: CriarTriagem, sessao: Session = Depends(obter_sessao)):
    """ 
    Regista a Triagem de Manchester para um episódio. 
    Define a prioridade e sinais vitais.
    """
    novo = Triagem(
        cod_epis=dados.cod_epis,
        prioridade=dados.prioridade,
        tensao_arterial=dados.tensao_arterial,
        temperatura=dados.temperatura,
        sintomas=dados.sintomas,
        observacoes=dados.observacoes,
        num_func_enfermeiro=dados.num_func_enfermeiro,
        data_h_triagem=datetime.now(timezone.utc)
    )
    sessao.add(novo)
    sessao.commit()
    sessao.refresh(novo)
    return novo

@router.post("/atos")
def registar_ato(dados: dict, sessao: Session = Depends(obter_sessao)):
    novo = Ato(
        tipo=dados["tipo"],
        data_h_inicio=dados.get("data_h_inicio", datetime.now(timezone.utc)),
        cod_epis=dados["cod_epis"],
        id_hosp=dados["id_hosp"],
        num_func=dados["num_func"],
        diagnostico=dados.get("diagnostico"),
        notas_clinicas=dados.get("notas_clinicas"),
        exame_fisico=dados.get("exame_fisico"),
        decisao_clinica=dados.get("decisao_clinica")
    )
    sessao.add(novo)
    
    # Se a decisão for ALTA (e não for internamento), fechar o episódio
    if dados.get("decisao_clinica") == "ALTA":
        episodio = sessao.get(EpisodioUrgencia, dados["cod_epis"])
        if episodio:
            episodio.data_h_saida = datetime.now(timezone.utc)
            sessao.add(episodio)
            
    sessao.commit()
    sessao.refresh(novo)
    return novo

@router.post("/prescricoes")
def registar_prescricao(dados: dict, sessao: Session = Depends(obter_sessao)):
    novo = Prescricao(
        cod_epis=dados["cod_epis"],
        medicamento=dados["medicamento"],
        dosagem=dados.get("dosagem"),
        num_func_medico=dados["num_func_medico"]
    )
    sessao.add(novo)
    sessao.commit()
    sessao.refresh(novo)
    return novo
