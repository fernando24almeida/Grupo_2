from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any

import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

DATABASE_URL = "postgresql://postgres:123456@localhost:5432/urgencias_g2"


@dataclass
class AnalyticsResult:
    metricas_modelo: Dict[str, float]
    importancia_features: List[Dict[str, Any]]
    afluencia_por_dia_semana: List[Dict[str, Any]]
    afluencia_por_periodo: List[Dict[str, Any]]
    previsoes_exemplo: List[Dict[str, Any]]


def classificar_periodo(hora: int) -> str:
    if 0 <= hora < 6:
        return "Madrugada"
    if 6 <= hora < 12:
        return "Manhã"
    if 12 <= hora < 18:
        return "Tarde"
    return "Noite"


def carregar_dados() -> pd.DataFrame:
    engine = create_engine(DATABASE_URL)

    query = text("""
        SELECT
            cod_epis,
            data_h_entr
        FROM episodio_urgencia
        WHERE data_h_entr IS NOT NULL
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        raise ValueError("Não existem episódios na tabela episodio_urgencia.")

    df["data_h_entr"] = pd.to_datetime(df["data_h_entr"])
    return df


def preparar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["data"] = df["data_h_entr"].dt.date
    df["hora"] = df["data_h_entr"].dt.hour
    df["dia_semana_num"] = df["data_h_entr"].dt.dayofweek  # 0=segunda, 6=domingo
    df["dia_semana"] = df["dia_semana_num"].map({
        0: "Segunda",
        1: "Terça",
        2: "Quarta",
        3: "Quinta",
        4: "Sexta",
        5: "Sábado",
        6: "Domingo",
    })
    df["mes"] = df["data_h_entr"].dt.month
    df["fim_semana"] = df["dia_semana_num"].isin([5, 6]).astype(int)
    df["periodo_dia"] = df["hora"].apply(classificar_periodo)

    # Agregação por dia + hora para representar afluência
    agrupado = (
        df.groupby(["data", "hora", "dia_semana_num", "dia_semana", "mes", "fim_semana", "periodo_dia"])
        .size()
        .reset_index(name="afluencia")
    )

    return agrupado


def treinar_modelo(df_modelo: pd.DataFrame) -> AnalyticsResult:
    df_encoded = pd.get_dummies(
        df_modelo[["hora", "dia_semana_num", "mes", "fim_semana", "periodo_dia"]],
        columns=["periodo_dia"],
        drop_first=False
    )

    X = df_encoded
    y = df_modelo["afluencia"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    modelo = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42
    )
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)

    metricas = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 3),
        "r2": round(float(r2_score(y_test, y_pred)), 3),
    }

    importancia = sorted(
        [
            {"feature": col, "importancia": round(float(imp), 4)}
            for col, imp in zip(X.columns, modelo.feature_importances_)
        ],
        key=lambda x: x["importancia"],
        reverse=True
    )

    afluencia_por_dia_semana = (
        df_modelo.groupby("dia_semana")["afluencia"]
        .mean()
        .reindex(["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"])
        .fillna(0)
        .round(2)
        .reset_index()
        .rename(columns={"afluencia": "media_afluencia"})
        .to_dict(orient="records")
    )

    afluencia_por_periodo = (
        df_modelo.groupby("periodo_dia")["afluencia"]
        .mean()
        .reindex(["Madrugada", "Manhã", "Tarde", "Noite"])
        .fillna(0)
        .round(2)
        .reset_index()
        .rename(columns={"afluencia": "media_afluencia"})
        .to_dict(orient="records")
    )

    exemplos = pd.DataFrame([
        {"hora": 9, "dia_semana_num": 0, "mes": 1, "fim_semana": 0, "periodo_dia": "Manhã"},
        {"hora": 15, "dia_semana_num": 4, "mes": 1, "fim_semana": 0, "periodo_dia": "Tarde"},
        {"hora": 21, "dia_semana_num": 5, "mes": 1, "fim_semana": 1, "periodo_dia": "Noite"},
    ])

    exemplos_encoded = pd.get_dummies(
        exemplos,
        columns=["periodo_dia"],
        drop_first=False
    )

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
        metricas_modelo=metricas,
        importancia_features=importancia,
        afluencia_por_dia_semana=afluencia_por_dia_semana,
        afluencia_por_periodo=afluencia_por_periodo,
        previsoes_exemplo=previsoes_exemplo,
    )


def executar_analytics() -> Dict[str, Any]:
    df = carregar_dados()
    df_modelo = preparar_dataset(df)
    resultado = treinar_modelo(df_modelo)

    return {
        "problema": "Deteção de padrões de afluência por período do dia e dia da semana com Random Forest",
        "metricas_modelo": resultado.metricas_modelo,
        "importancia_features": resultado.importancia_features,
        "afluencia_por_dia_semana": resultado.afluencia_por_dia_semana,
        "afluencia_por_periodo": resultado.afluencia_por_periodo,
        "previsoes_exemplo": resultado.previsoes_exemplo,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(executar_analytics(), indent=2, ensure_ascii=False))