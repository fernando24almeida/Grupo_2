from __future__ import annotations
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Any

import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# =============================================================================
# MÓDULO DE INTELIGÊNCIA ARTIFICIAL: PREVISÃO DE AFLUÊNCIA HOSPITALAR
# 
# EXPLICAÇÃO PARA ALUNOS:
# Este ficheiro é o "cérebro" estatístico do projeto. O seu objetivo é olhar 
# para o passado (histórico de entradas no hospital) e tentar adivinhar o 
# futuro (quantas pessoas virão ao hospital em certas horas e dias).
# =============================================================================

# Configuração robusta de imports para o backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from app.core.config import configuracoes
    DATABASE_URL = configuracoes.DATABASE_URL
except ImportError:
    # Caso a aplicação não esteja a correr no servidor real, usa esta morada padrão
    DATABASE_URL = "postgresql://postgres:admin@127.0.0.1:5432/urgencias_g2"

@dataclass
class AnalyticsResult:
    """
    Esta 'caixa' guarda os resultados da nossa análise para os enviar ao ecrã.
    Guarda: quão bom é o modelo, o que é mais importante (ex: a hora), 
    as médias de pessoas e algumas previsões de exemplo.
    """
    metricas_modelo: Dict[str, float]
    importancia_features: List[Dict[str, Any]]
    afluencia_por_dia_semana: List[Dict[str, Any]]
    afluencia_por_periodo: List[Dict[str, Any]]
    previsoes_exemplo: List[Dict[str, Any]]


def classificar_periodo(hora: int) -> str:
    """
    Função simples para agrupar as 24 horas do dia em 4 blocos amigáveis:
    Madrugada, Manhã, Tarde e Noite.
    """
    if 0 <= hora < 6:
        return "Madrugada"
    if 6 <= hora < 12:
        return "Manhã"
    if 12 <= hora < 18:
        return "Tarde"
    return "Noite"


def calcular_medias_simples(df_modelo: pd.DataFrame, coluna: str) -> List[Dict[str, Any]]:
    """
    Calcula a média de pessoas que costumam vir por cada dia da semana 
    ou por cada período (ex: 'Às Segundas vêm em média 15 pessoas').
    """
    if df_modelo.empty:
        return []
    
    if coluna == "dia_semana":
        ordem = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    else:
        ordem = ["Madrugada", "Manhã", "Tarde", "Noite"]

    return (
        df_modelo.groupby(coluna)["afluencia"]
        .mean()
        .reindex(ordem)
        .fillna(0)
        .round(2)
        .reset_index()
        .rename(columns={"afluencia": "media_afluencia"})
        .to_dict(orient="records")
    )


def carregar_dados() -> tuple[pd.DataFrame, str]:
    """
    Vai buscar à base de dados SQL a lista de todos os doentes que entraram.
    O Pandas (pd) transforma essa lista numa tabela fácil de ler para o computador.
    """
    engine = create_engine(DATABASE_URL)
    query = text("SELECT cod_epis, data_h_entr FROM episodio_urgencia WHERE data_h_entr IS NOT NULL")

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            if not df.empty:
                df["data_h_entr"] = pd.to_datetime(df["data_h_entr"])
            return df, ""
    except Exception as e:
        return pd.DataFrame(), str(e)


def preparar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Esta função 'limpa' os dados. Ela separa a data em partes:
    Mês, Dia da Semana, Hora, etc. No final, conta quantos doentes 
    estavam no hospital em cada hora de cada dia.
    """
    if df.empty:
        return pd.DataFrame()
        
    df = df.copy()
    df["data"] = df["data_h_entr"].dt.date
    df["hora"] = df["data_h_entr"].dt.hour
    df["dia_semana_num"] = df["data_h_entr"].dt.dayofweek
    df["dia_semana"] = df["dia_semana_num"].map({
        0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"
    })
    df["mes"] = df["data_h_entr"].dt.month
    df["fim_semana"] = df["dia_semana_num"].isin([5, 6]).astype(int)
    df["periodo_dia"] = df["hora"].apply(classificar_periodo)

    agrupado = (
        df.groupby(["data", "hora", "dia_semana_num", "dia_semana", "mes", "fim_semana", "periodo_dia"])
        .size()
        .reset_index(name="afluencia")
    )
    return agrupado


def treinar_modelo(df_modelo: pd.DataFrame) -> AnalyticsResult:
    """
    AQUI ACONTECE A MAGIA (IA):
    1. Preparamos os dados para o algoritmo.
    2. Usamos o 'Random Forest' (uma floresta de decisões) para aprender os padrões.
    3. Testamos se ele aprendeu bem (métricas mae e r2).
    4. Guardamos o que ele acha mais importante para prever a afluência.
    """
    if df_modelo.empty or len(df_modelo) < 5:
        return AnalyticsResult(
            {"mae": 0, "r2": 0}, [], 
            calcular_medias_simples(df_modelo, "dia_semana"),
            calcular_medias_simples(df_modelo, "periodo_dia"),
            []
        )

    # Transforma texto em números para o modelo entender (One-Hot Encoding)
    df_encoded = pd.get_dummies(
        df_modelo[["hora", "dia_semana_num", "mes", "fim_semana", "periodo_dia"]],
        columns=["periodo_dia"],
        drop_first=False
    )

    X = df_encoded # O que usamos para prever (Hora, Dia...)
    y = df_modelo["afluencia"] # O que queremos adivinhar (Quantas pessoas)

    # Separamos uma parte para 'estudar' e outra para 'fazer o exame' (teste)
    if len(df_modelo) < 10:
        X_train, X_test, y_train, y_test = X, X, y, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Criamos a Inteligência Artificial (Floresta de Decisão)
    modelo = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    modelo.fit(X_train, y_train) # Treinar!

    y_pred = modelo.predict(X_test) # Fazer o teste

    # Ver se as notas do exame foram boas
    metricas = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 3), # Erro médio de pessoas
        "r2": round(float(r2_score(y_test, y_pred)), 3), # De 0 a 1, quão perto estamos da perfeição
    }

    # Ver o que o modelo achou mais importante (ex: 'A hora é mais importante que o mês')
    importancia = sorted([
        {"feature": col, "importancia": round(float(imp), 4)}
        for col, imp in zip(X.columns, modelo.feature_importances_)
    ], key=lambda x: x["importancia"], reverse=True)

    # Criar alguns exemplos de 'bola de cristal' para mostrar no Dashboard
    exemplos = pd.DataFrame([
        {"hora": 10, "dia_semana_num": 0, "mes": 5, "fim_semana": 0, "periodo_dia": "Manhã"},
        {"hora": 16, "dia_semana_num": 4, "mes": 5, "fim_semana": 0, "periodo_dia": "Tarde"},
        {"hora": 22, "dia_semana_num": 6, "mes": 5, "fim_semana": 1, "periodo_dia": "Noite"},
    ])
    exemplos_encoded = pd.get_dummies(exemplos, columns=["periodo_dia"], drop_first=False)
    exemplos_encoded = exemplos_encoded.reindex(columns=X.columns, fill_value=0)
    previsoes = modelo.predict(exemplos_encoded)

    previsoes_exemplo = [
        {
            "hora": int(exemplos.iloc[i]["hora"]),
            "dia_semana_num": int(exemplos.iloc[i]["dia_semana_num"]),
            "periodo_dia": exemplos.iloc[i]["periodo_dia"],
            "afluencia_prevista": round(float(previsoes[i]), 2),
        }
        for i in range(len(exemplos))
    ]

    return AnalyticsResult(
        metricas,
        importancia,
        calcular_medias_simples(df_modelo, "dia_semana"),
        calcular_medias_simples(df_modelo, "periodo_dia"),
        previsoes_exemplo
    )


def executar_analytics() -> Dict[str, Any]:
    """
    Função principal que corre todo o processo:
    Carrega -> Prepara -> Treina -> Devolve os resultados.
    """
    df, erro = carregar_dados()
    
    if df.empty:
        return {
            "status": "warning",
            "message": f"Erro BD: {erro}" if erro else "Base de dados sem registos.",
            "problema": "Impossível analisar dados",
            "metricas_modelo": {"mae": 0, "r2": 0},
            "importancia_features": [],
            "afluencia_por_dia_semana": [],
            "afluencia_por_periodo": [],
            "previsoes_exemplo": []
        }

    df_modelo = preparar_dataset(df)
    resultado = treinar_modelo(df_modelo)

    return {
        "status": "success",
        "problema": "Deteção de padrões de afluência por período do dia e dia da semana com Random Forest",
        "metricas_modelo": resultado.metricas_modelo,
        "importancia_features": resultado.importancia_features,
        "afluencia_por_dia_semana": resultado.afluencia_por_dia_semana,
        "afluencia_por_periodo": resultado.afluencia_por_periodo,
        "previsoes_exemplo": resultado.previsoes_exemplo
    }

# Se corrermos este ficheiro sozinho no terminal, ele mostra os resultados no ecrã
if __name__ == "__main__":
    import json
    print(json.dumps(executar_analytics(), indent=2, ensure_ascii=False))
