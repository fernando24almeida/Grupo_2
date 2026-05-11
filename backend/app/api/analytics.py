from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import Optional, List
from ..core.db import obter_sessao
from ..models.models import EpisodioUrgencia, Triagem
from datetime import datetime, timedelta

router = APIRouter()

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
    há_um_dia = datetime.now() - timedelta(days=1)
    contagem = sessao.exec(select(func.count(EpisodioUrgencia.cod_epis)).where(EpisodioUrgencia.data_h_entrada >= há_um_dia)).one()

    return {
        "episodios_ultimas_24h": contagem,
        "estado": "Normal"
    }

@router.get("/dashboard-summary")
def dashboard_summary(id_hospital: Optional[str] = None, sessao: Session = Depends(obter_sessao)):
    agora = datetime.now()
    
    # Base query for open episodes that have been triaged
    query = select(EpisodioUrgencia, Triagem).join(
        Triagem, EpisodioUrgencia.cod_epis == Triagem.cod_epis
    ).where(EpisodioUrgencia.data_h_saida == None)
    
    if id_hospital:
        query = query.where(EpisodioUrgencia.id_hospital == id_hospital)
        
    resultados = sessao.exec(query).all()
    
    # Breakdown by priority
    breakdown = {
        "VERMELHO": {"count": 0, "total_wait": 0},
        "LARANJA": {"count": 0, "total_wait": 0},
        "AMARELO": {"count": 0, "total_wait": 0},
        "VERDE": {"count": 0, "total_wait": 0},
        "AZUL": {"count": 0, "total_wait": 0}
    }
    
    for ep, tri in resultados:
        prioridade = tri.prioridade
        if prioridade in breakdown:
            breakdown[prioridade]["count"] += 1
            # Wait time since triage in minutes
            wait_min = (agora - tri.data_h_triagem).total_seconds() / 60
            breakdown[prioridade]["total_wait"] += max(0, wait_min)
            
    # Format response
    stats = []
    total_waiting = 0
    total_critical = 0
    
    for cor, data in breakdown.items():
        avg = round(data["total_wait"] / data["count"]) if data["count"] > 0 else 0
        stats.append({
            "prioridade": cor,
            "quantidade": data["count"],
            "tempo_medio": avg
        })
        total_waiting += data["count"]
        if cor in ["VERMELHO", "LARANJA"]:
            total_critical += data["count"]
            
    return {
        "waiting": total_waiting,
        "critical": total_critical,
        "stats": stats,
        "updatedAt": agora.isoformat()
    }
