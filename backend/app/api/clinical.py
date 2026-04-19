from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func, union_all
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.db import obter_sessao
from ..models.models import Utente, EpisodioUrgencia, Triagem, Ato, Prescricao, Internamento, Hospital, Envolve, FuncionarioHospital
from ..core.security import RoleChecker

router = APIRouter()
admin_only = RoleChecker(["ADMIN"])

# SCHEMAS
class CriarEpisodio(BaseModel):
    id_utente: int
    id_hospital: str
    data_h_entrada: Optional[datetime] = None
    sintomas: Optional[str] = None
    observacoes: Optional[str] = None

class AtualizarUtente(BaseModel):
    nome: Optional[str] = None
    telemovel: Optional[str] = None
    morada: Optional[str] = None
    sexo: Optional[str] = None
    localidade: Optional[str] = None
    data_nascimento: Optional[datetime] = None

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

@router.post("/utentes", response_model=Utente)
def criar_utente(utente: Utente, sessao: Session = Depends(obter_sessao)):
    sessao.add(utente)
    sessao.commit()
    sessao.refresh(utente)
    return utente

@router.get("/utentes", response_model=List[Utente])
def ler_utentes(sessao: Session = Depends(obter_sessao)):
    utentes = sessao.exec(select(Utente)).all()
    return utentes

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

# TRIAGEM
@router.post("/triagens", response_model=Triagem)
def criar_triagem(triagem: Triagem, sessao: Session = Depends(obter_sessao)):
    sessao.add(triagem)
    sessao.commit()
    sessao.refresh(triagem)
    return triagem

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
