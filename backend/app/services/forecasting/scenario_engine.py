"""
Motor de cenários para forecast de tonelagem (horizonte 5 anos).

Gera 3 cenários (base, otimista, pessimista) ajustando as variáveis
exógenas de acordo com premissas macro e climáticas.

Para horizonte longo (>12m), os choques são aplicados com convergência
gradual ao cenário base (mean-reversion), refletindo que choques
extremos não se sustentam por 5 anos.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Premissas por cenário para variáveis-chave.
# Cada valor é o choque aplicado como multiplicador: valor_projetado = base × (1 + choque).
# Exceção: variáveis "aditivas" (ONI, ton_yoy) usam choque absoluto somado ao base.
SCENARIO_ASSUMPTIONS = {
    "base": {
        "cambio": 0.0,
        "ibc_br": 0.0,
        "selic": 0.0,
        "ipca": 0.0,
        "navios": 0.0,
        "tempo_espera": 0.0,
        "tempo_atracacao": 0.0,
        "precipitacao": 0.0,
        "oni": 0.0,
        "safra": 0.0,
        "descricao": "Cenário base: variáveis nos níveis atuais",
    },
    "otimista": {
        "cambio": 0.10,          # BRL 10% mais fraco → exportação sobe
        "ibc_br": 0.05,          # PIB +5%
        "selic": -0.15,          # Selic cai 15% relativo
        "ipca": -0.05,           # Inflação menor
        "navios": 0.10,          # +10% navios atendidos (expansão de capacidade)
        "tempo_espera": -0.20,   # -20% tempo de espera (eficiência operacional)
        "tempo_atracacao": -0.10, # -10% tempo de operação
        "precipitacao": 0.10,    # Chuva acima da média
        "oni": -0.5,             # La Niña moderada (ADITIVO, não multiplicador)
        "safra": 0.12,           # Safra recorde (+12%)
        "descricao": "Cenário otimista: expansão portuária, câmbio favorável, safra recorde",
    },
    "pessimista": {
        "cambio": -0.10,         # BRL 10% mais forte → exportação cai
        "ibc_br": -0.05,         # Recessão
        "selic": 0.20,           # Selic sobe 20% relativo
        "ipca": 0.08,            # Inflação maior
        "navios": -0.08,         # -8% navios (demanda menor)
        "tempo_espera": 0.30,    # +30% tempo de espera (congestionamento)
        "tempo_atracacao": 0.15, # +15% tempo de operação (ineficiência)
        "precipitacao": -0.30,   # Seca severa
        "oni": 1.5,              # El Niño forte (ADITIVO)
        "safra": -0.15,          # Quebra de safra (-15%)
        "descricao": "Cenário pessimista: recessão, congestionamento portuário, quebra de safra",
    },
}

# Features com choque aditivo (não multiplicativo).
# ONI é um índice absoluto (-2 a +2), ton_yoy é taxa percentual.
_ADDITIVE_FEATURES = {"oni"}


class ScenarioEngine:
    """Gera cenários macro + clima para forecast de tonelagem."""

    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names

    def generate_exog_scenarios(
        self,
        df: pd.DataFrame,
        steps: int = 60,
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
                shock = self._get_shock_for_feature(col, assumptions)

                # Mean-reversion: choque decai 20% ao ano para horizontes longos
                # Ano 1: 100% do choque, Ano 2: 80%, Ano 3: 64%, Ano 4: 51%, Ano 5: 41%
                is_additive = self._is_additive_feature(col)
                values = []
                for i in range(steps):
                    year_fraction = i / 12
                    decay = 0.8 ** year_fraction  # 20% decay por ano
                    effective_shock = shock * decay

                    if is_additive:
                        # Choque absoluto somado ao valor base (ex: ONI)
                        projected = base_val + effective_shock
                    else:
                        # Choque multiplicativo (ex: câmbio, navios)
                        projected = base_val * (1 + effective_shock)

                    # Sazonalidade para precipitação
                    if "precip" in col:
                        projected *= (1 + 0.3 * np.sin(2 * np.pi * (i + last_date.month) / 12))

                    values.append(projected)

                future_data[col] = values

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

        Inclui projeção anual para cada um dos 5 anos e variação
        acumulada no período completo.
        """
        last_year = df.index[-1].year - 1
        yearly_ref = df[df.index.year == last_year]["tonelagem"].sum()

        scenarios_out = []
        for name, forecast in forecasts.items():
            assumptions = SCENARIO_ASSUMPTIONS.get(name, {})
            previsoes_anuais = forecast.get("previsoes_anuais", [])
            previsoes_mensais = forecast.get("previsoes_mensais", [])

            # Separa anos completos (12 meses) de anos parciais
            anos_completos = [
                p for p in previsoes_anuais
                if p.get("meses_previstos", 12) == 12
            ]
            anos_parciais = [
                p for p in previsoes_anuais
                if p.get("meses_previstos", 12) < 12
            ]

            # Total no horizonte (apenas anos completos para métricas)
            total_horizonte = sum(
                p.get("tonelagem_anual", 0) for p in previsoes_anuais
            )

            # CAGR calculado sobre o último ano COMPLETO vs. referência
            if anos_completos:
                ultimo_completo = anos_completos[-1]
                ton_ultimo = ultimo_completo.get("tonelagem_anual", 0)
                n_anos = len(anos_completos)
                variacao_final = round((ton_ultimo / yearly_ref - 1) * 100, 1) if yearly_ref > 0 else None
                cagr = None
                if yearly_ref > 0 and ton_ultimo > 0 and n_anos > 0:
                    cagr = round(((ton_ultimo / yearly_ref) ** (1 / n_anos) - 1) * 100, 1)
            else:
                variacao_final = None
                cagr = None

            # Marca anos parciais no output
            for p in anos_parciais:
                p["parcial"] = True

            scenarios_out.append({
                "cenario": name,
                "descricao": assumptions.get("descricao", ""),
                "horizonte_anos": len(anos_completos),
                "horizonte_anos_total": len(previsoes_anuais),
                "tonelagem_ano_referencia": round(yearly_ref, 0),
                "ano_referencia": last_year,
                "previsoes_anuais": previsoes_anuais,
                "variacao_acumulada_pct": variacao_final,
                "cagr_pct": cagr,
                "premissas": {
                    k: v for k, v in assumptions.items()
                    if k != "descricao"
                },
                "nota_mean_reversion": (
                    "Choques decaem 20% ao ano (mean-reversion). "
                    "Ano 1: 100% do choque, Ano 5: ~41%. "
                    "Reflete que condições extremas não se sustentam por 5 anos."
                ),
            })

        return {
            "cenarios": scenarios_out,
            "ano_referencia": last_year,
            "horizonte": "5 anos",
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
        elif "navios" in col_lower:
            return assumptions.get("navios", 0)
        elif "tempo_espera" in col_lower:
            return assumptions.get("tempo_espera", 0)
        elif "tempo_atracacao" in col_lower:
            return assumptions.get("tempo_atracacao", 0)
        elif "precip" in col_lower:
            return assumptions.get("precipitacao", 0)
        elif "oni" in col_lower:
            return assumptions.get("oni", 0)
        elif "safra" in col_lower:
            return assumptions.get("safra", 0)
        elif "ton_lag" in col_lower or "ton_ma" in col_lower or "ton_yoy" in col_lower:
            return 0  # Derivadas do target: sem choque
        return 0

    @staticmethod
    def _is_additive_feature(col: str) -> bool:
        """Verifica se a feature usa choque aditivo (não multiplicativo)."""
        col_lower = col.lower()
        for pattern in _ADDITIVE_FEATURES:
            if pattern in col_lower:
                return True
        return False
