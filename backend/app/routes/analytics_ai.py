from fastapi import APIRouter
from ai.analytics_afluencia import executar_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/afluencia-random-forest")
def analytics_afluencia_random_forest():
    return executar_analytics()