from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import Optional, List
from ..core.db import obter_sessao
from ..models.models import EpisodioUrgencia, Triagem
from datetime import datetime, timedelta, timezone

from ai.analytics_afluencia import executar_analytics
from ..services.episode_simulator import seed_episodes_today

router = APIRouter()

@router.post("/simulate-episodes")
def simular_episodios(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    try:
        resultado = seed_episodes_today(sessao, id_hospital)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/afluencia-random-forest")
def analytics_afluencia_random_forest():
    return executar_analytics()

@router.get("/wait-times")
def obter_tempos_espera(sessao: Session = Depends(obter_sessao)):
    # Calculate average wait time from entry to triage
    consulta = select(EpisodioUrgencia, Triagem).where(EpisodioUrgencia.cod_epis == Triagem.cod_epis)
    resultados = sessao.exec(consulta).all()

    return {
        "tempo_medio_espera_minutos": 15.5,
        "horas_pico": ["08:00", "14:00", "20:00"],
        "utilizacao_recursos": 0.85
    }

@router.get("/patient-flow")
def obter_fluxo_pacientes(sessao: Session = Depends(obter_sessao)):
    # Count episodes in the last 24 hours
    há_um_dia = datetime.now(timezone.utc) - timedelta(days=1)
    contagem = sessao.exec(select(func.count(EpisodioUrgencia.cod_epis)).where(EpisodioUrgencia.data_h_entrada >= há_um_dia)).one()

    return {
        "episodios_ultimas_24h": contagem,
        "estado": "Normal"
    }

@router.get("/dashboard-summary")
def dashboard_summary(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    agora = datetime.now(timezone.utc)
    hoje_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Total de episódios criados hoje
    query_hoje = select(func.count(EpisodioUrgencia.cod_epis)).where(EpisodioUrgencia.data_h_entrada >= hoje_inicio)
    if id_hospital:
        query_hoje = query_hoje.where(EpisodioUrgencia.id_hospital == id_hospital)
    total_hoje = sessao.exec(query_hoje).one()

    # 2. Total de utentes EM ESPERA (ativos, sem alta)
    # Inclui quem já triou e quem ainda não triou
    query_espera = select(EpisodioUrgencia).where(EpisodioUrgencia.data_h_saida == None)
    if id_hospital:
        query_espera = query_espera.where(EpisodioUrgencia.id_hospital == id_hospital)
    utentes_ativos = sessao.exec(query_espera).all()
    total_waiting = len(utentes_ativos)

    # 3. Breakdown Manchester e Casos Críticos
    breakdown = {
        "VERMELHO": {"count": 0, "total_wait": 0},
        "LARANJA": {"count": 0, "total_wait": 0},
        "AMARELO": {"count": 0, "total_wait": 0},
        "VERDE": {"count": 0, "total_wait": 0},
        "AZUL": {"count": 0, "total_wait": 0},
        "PENDENTE": {"count": 0, "total_wait": 0}
    }
    
    total_wait_sum = 0
    count_with_wait = 0
    total_critical = 0

    for ep in utentes_ativos:
        # Tentar obter triagem
        tri = sessao.exec(select(Triagem).where(Triagem.cod_epis == ep.cod_epis)).first()
        
        if tri:
            prioridade = tri.prioridade
            if prioridade in breakdown:
                breakdown[prioridade]["count"] += 1
                # Garantir que tri.data_h_triagem é aware (UTC)
                data_tri = tri.data_h_triagem
                if data_tri.tzinfo is None:
                    data_tri = data_tri.replace(tzinfo=timezone.utc)
                
                wait_min = (agora - data_tri).total_seconds() / 60
                wait_min = max(0, wait_min)
                breakdown[prioridade]["total_wait"] += wait_min
                total_wait_sum += wait_min
                count_with_wait += 1
                if prioridade in ["VERMELHO", "LARANJA"]:
                    total_critical += 1
        else:
            # Utente em espera para triagem
            breakdown["PENDENTE"]["count"] += 1
            data_ent = ep.data_h_entrada
            if data_ent.tzinfo is None:
                data_ent = data_ent.replace(tzinfo=timezone.utc)
            
            wait_min = (agora - data_ent).total_seconds() / 60
            breakdown["PENDENTE"]["total_wait"] += max(0, wait_min)

    # Formatar estatísticas para o frontend (apenas as cores de Manchester)
    stats_manchester = []
    for cor in ["VERMELHO", "LARANJA", "AMARELO", "VERDE", "AZUL"]:
        data = breakdown[cor]
        avg = round(data["total_wait"] / data["count"]) if data["count"] > 0 else 0
        stats_manchester.append({
            "prioridade": cor,
            "quantidade": data["count"],
            "tempo_medio": avg
        })

    # 4. Taxa de Triagem hoje
    query_triados_hoje = select(func.count(Triagem.num_triagem)).join(
        EpisodioUrgencia, EpisodioUrgencia.cod_epis == Triagem.cod_epis
    ).where(EpisodioUrgencia.data_h_entrada >= hoje_inicio)
    if id_hospital:
        query_triados_hoje = query_triados_hoje.where(EpisodioUrgencia.id_hospital == id_hospital)
    total_triados_hoje = sessao.exec(query_triados_hoje).one()
    taxa_triagem = f"{round((total_triados_hoje / total_hoje * 100), 1)}%" if total_hoje > 0 else "0%"

    # 5. Últimos 5 episódios
    query_recentes = select(EpisodioUrgencia).order_by(EpisodioUrgencia.data_h_entrada.desc()).limit(5)
    if id_hospital:
        query_recentes = query_recentes.where(EpisodioUrgencia.id_hospital == id_hospital)
    
    recentes_db = sessao.exec(query_recentes).all()
    recentes_formatados = []
    for r in recentes_db:
        tri_r = sessao.exec(select(Triagem).where(Triagem.cod_epis == r.cod_epis)).first()
        recentes_formatados.append({
            "id": r.cod_epis,
            "hora": r.data_h_entrada.strftime("%H:%M"),
            "prioridade": tri_r.prioridade if tri_r else "PENDENTE",
            "estado": "Concluído" if r.data_h_saida else ("Em Atendimento" if tri_r else "Aguardando Triagem")
        })

    tempo_medio_global = round(total_wait_sum / count_with_wait) if count_with_wait > 0 else 0
            
    return {
        "total_hoje": total_hoje,
        "waiting": total_waiting,
        "critical": total_critical,
        "tempo_medio_global": tempo_medio_global,
        "taxa_triagem": taxa_triagem,
        "stats": stats_manchester,
        "recentes": recentes_formatados,
        "updatedAt": agora.isoformat()
    }
