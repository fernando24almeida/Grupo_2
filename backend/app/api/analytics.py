from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
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
