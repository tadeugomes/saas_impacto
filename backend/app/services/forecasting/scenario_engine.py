"""
Motor de cenários para forecast de tonelagem.

Gera 3 cenários (base, otimista, pessimista) ajustando as variáveis
exógenas de acordo com premissas macro e climáticas.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Premissas por cenário para variáveis-chave
SCENARIO_ASSUMPTIONS = {
    "base": {
        "cambio": 0.0,           # Sem variação
        "ibc_br": 0.0,
        "selic": 0.0,
        "ipca": 0.0,
        "precipitacao": 0.0,     # Normal
        "oni": 0.0,              # Neutro
        "safra": 0.0,
        "descricao": "Cenário base: variáveis macro e climáticas nos níveis atuais",
    },
    "otimista": {
        "cambio": 0.10,          # BRL 10% mais fraco → exportação sobe
        "ibc_br": 0.02,          # Atividade +2%
        "selic": -0.15,          # Selic cai 15% relativo
        "ipca": -0.05,           # Inflação menor
        "precipitacao": 0.10,    # Chuva acima da média (bom para safra)
        "oni": -0.5,             # La Niña moderada (bom para Sul/Sudeste)
        "safra": 0.12,           # Safra recorde (+12%)
        "descricao": "Cenário otimista: câmbio favorável, safra recorde, La Niña moderada",
    },
    "pessimista": {
        "cambio": -0.10,         # BRL 10% mais forte → exportação cai
        "ibc_br": -0.02,         # Recessão leve
        "selic": 0.15,           # Selic sobe
        "ipca": 0.05,            # Inflação maior
        "precipitacao": -0.30,   # Seca severa
        "oni": 1.5,              # El Niño forte
        "safra": -0.15,          # Quebra de safra (-15%)
        "descricao": "Cenário pessimista: BRL forte, El Niño forte, quebra de safra",
    },
}


class ScenarioEngine:
    """Gera cenários macro + clima para forecast de tonelagem."""

    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names

    def generate_exog_scenarios(
        self,
        df: pd.DataFrame,
        steps: int = 12,
    ) -> Dict[str, pd.DataFrame]:
        """
        Gera DataFrames de exógenas futuras para cada cenário.

        Projeta cada variável como o último valor observado × (1 + choque).

        Returns:
            Dict {"base": df_exog, "otimista": df_exog, "pessimista": df_exog}
        """
        if not self.feature_names:
            return {name: None for name in SCENARIO_ASSUMPTIONS}

        # Última observação de cada feature
        last_values = {}
        for col in self.feature_names:
            if col in df.columns:
                vals = df[col].dropna()
                last_values[col] = float(vals.iloc[-1]) if len(vals) > 0 else 0.0
            else:
                last_values[col] = 0.0

        # Gera index futuro
        last_date = df.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.MonthBegin(1),
            periods=steps,
            freq="MS",
        )

        scenarios = {}
        for scenario_name, assumptions in SCENARIO_ASSUMPTIONS.items():
            if scenario_name == "descricao":
                continue

            future_data = {}
            for col in self.feature_names:
                base_val = last_values.get(col, 0.0)

                # Aplica choque da premissa ao col relevante
                shock = self._get_shock_for_feature(col, assumptions)
                projected = base_val * (1 + shock)

                # Adiciona sazonalidade para precipitação
                if "precip" in col:
                    future_data[col] = [
                        projected * (1 + 0.3 * np.sin(2 * np.pi * (i + last_date.month) / 12))
                        for i in range(steps)
                    ]
                else:
                    future_data[col] = [projected] * steps

            scenarios[scenario_name] = pd.DataFrame(
                future_data, index=future_dates
            )

        return scenarios

    def format_scenarios_response(
        self,
        forecasts: Dict[str, Dict],
        df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Formata os resultados dos 3 cenários para a resposta da API.
        """
        # Tonelagem do último ano completo
        last_year = df.index[-1].year - 1
        yearly = df[df.index.year == last_year]["tonelagem"].sum()

        scenarios_out = []
        for name, forecast in forecasts.items():
            assumptions = SCENARIO_ASSUMPTIONS.get(name, {})
            previsoes = forecast.get("previsoes", [])
            total_previsto = sum(p.get("tonelagem_prevista", 0) for p in previsoes)
            variacao = round((total_previsto / yearly - 1) * 100, 1) if yearly > 0 else None

            scenarios_out.append({
                "cenario": name,
                "descricao": assumptions.get("descricao", ""),
                "tonelagem_anual_prevista": round(total_previsto, 0),
                "tonelagem_ano_anterior": round(yearly, 0),
                "variacao_pct": variacao,
                "previsoes_mensais": previsoes,
                "premissas": {
                    k: v for k, v in assumptions.items()
                    if k != "descricao"
                },
            })

        return {
            "cenarios": scenarios_out,
            "ano_referencia": last_year,
        }

    @staticmethod
    def _get_shock_for_feature(col: str, assumptions: Dict) -> float:
        """Mapeia nome da feature para o choque do cenário."""
        col_lower = col.lower()

        if "cambio" in col_lower or "ptax" in col_lower:
            return assumptions.get("cambio", 0)
        elif "ibc" in col_lower:
            return assumptions.get("ibc_br", 0)
        elif "selic" in col_lower:
            return assumptions.get("selic", 0)
        elif "ipca" in col_lower:
            return assumptions.get("ipca", 0)
        elif "precip" in col_lower:
            return assumptions.get("precipitacao", 0)
        elif "oni" in col_lower:
            return assumptions.get("oni", 0)
        elif "safra" in col_lower:
            return assumptions.get("safra", 0)
        elif "ton_lag" in col_lower or "ton_ma" in col_lower:
            return 0  # Lags mantidos
        return 0
