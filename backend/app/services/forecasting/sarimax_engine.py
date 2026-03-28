"""
Motor SARIMAX para forecast de tonelagem portuária.

Horizonte: até 60 meses (5 anos), dividido em 3 faixas:
  - Curto prazo (1-12m): SARIMAX com exógenas operacionais + clima
  - Médio prazo (13-36m): SARIMAX com exógenas macro + safra
  - Longo prazo (37-60m): Tendência estrutural + sazonalidade

Seleção parcimoniosa: max 3-4 exógenas (regra 1:25 obs/feature).
Stepwise AIC com penalidade mínima de 2 pontos.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Horizonte padrão: 5 anos
DEFAULT_HORIZON_MONTHS = 60

# Máximo de exógenas por número de observações (regra 1:25)
MAX_EXOG_RATIO = 25


class SarimaxEngine:
    """Motor SARIMAX para previsão de throughput portuário (até 5 anos)."""

    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 12),
    ):
        self.order = order
        self.seasonal_order = seasonal_order
        self._model = None
        self._results = None
        self._feature_names: List[str] = []
        self._target_name = "tonelagem"

    def fit(
        self,
        df: pd.DataFrame,
        target: str = "tonelagem",
        exog_cols: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Treina o modelo SARIMAX com seleção parcimoniosa de features.

        A seleção respeita a regra de 1 feature para cada 25 observações.
        Usa stepwise AIC com penalidade mínima de 2 pontos.
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        self._target_name = target
        y = df[target].dropna()

        # Limite de features baseado no tamanho da amostra
        max_features = max(1, len(y) // MAX_EXOG_RATIO)

        if exog_cols is None:
            exog_cols = self._stepwise_select(df, target, max_features)

        # Limita ao máximo permitido
        exog_cols = exog_cols[:max_features]
        self._feature_names = exog_cols

        if exog_cols:
            exog = df.loc[y.index, exog_cols].ffill().fillna(0)
        else:
            exog = None

        try:
            self._model = SARIMAX(
                y, exog=exog,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            self._results = self._model.fit(disp=False, maxiter=200)

            return {
                "aic": round(self._results.aic, 2),
                "bic": round(self._results.bic, 2),
                "n_obs": int(self._results.nobs),
                "n_features": len(exog_cols),
                "max_features_permitido": max_features,
                "features_used": exog_cols,
                "regra_parcimonia": f"1:{MAX_EXOG_RATIO} (max {max_features} vars para {len(y)} obs)",
            }
        except Exception as e:
            logger.warning("sarimax_fit_error: %s — fallback SARIMA puro", e)
            self._feature_names = []
            try:
                self._model = SARIMAX(
                    y, order=self.order, seasonal_order=self.seasonal_order,
                    enforce_stationarity=False, enforce_invertibility=False,
                )
                self._results = self._model.fit(disp=False, maxiter=200)
                return {
                    "aic": round(self._results.aic, 2),
                    "n_obs": int(self._results.nobs),
                    "n_features": 0,
                    "features_used": [],
                    "fallback": "SARIMA puro (exógenas causaram erro)",
                }
            except Exception as e2:
                raise RuntimeError(f"SARIMAX e SARIMA falharam: {e2}") from e

    def forecast(
        self,
        steps: int = DEFAULT_HORIZON_MONTHS,
        exog_future: Optional[pd.DataFrame] = None,
        confidence_levels: List[float] = [0.80, 0.95],
    ) -> Dict[str, Any]:
        """
        Gera forecast de até 60 meses (5 anos).

        Para horizonte >12 meses, a incerteza cresce naturalmente
        nos intervalos de confiança — o modelo é honesto sobre isso.

        Returns:
            Dict com previsões anuais e mensais + IC + horizonte
        """
        if self._results is None:
            raise RuntimeError("Modelo não treinado. Chame fit() primeiro.")

        forecast_result = self._results.get_forecast(steps=steps, exog=exog_future)
        predicted = forecast_result.predicted_mean

        # Monta resultado mensal
        previsoes_mensais = []
        for level in confidence_levels:
            alpha = 1 - level
            ci = forecast_result.conf_int(alpha=alpha)

            for i in range(steps):
                date_str = (
                    predicted.index[i].strftime("%Y-%m")
                    if hasattr(predicted.index[i], "strftime")
                    else str(predicted.index[i])
                )

                entry = None
                for e in previsoes_mensais:
                    if e["periodo"] == date_str:
                        entry = e
                        break

                if entry is None:
                    entry = {
                        "periodo": date_str,
                        "ano": int(date_str[:4]),
                        "mes": int(date_str[5:7]),
                        "tonelagem_prevista": round(max(0, float(predicted.iloc[i])), 0),
                    }
                    previsoes_mensais.append(entry)

                pct = int(level * 100)
                entry[f"ic_{pct}_inferior"] = round(max(0, float(ci.iloc[i, 0])), 0)
                entry[f"ic_{pct}_superior"] = round(max(0, float(ci.iloc[i, 1])), 0)

        # Agrega por ano
        previsoes_anuais = self._aggregate_by_year(previsoes_mensais)

        # Classifica por horizonte
        horizontes = {
            "curto_prazo": {"meses": "1-12", "previsoes": previsoes_mensais[:12]},
            "medio_prazo": {"meses": "13-36", "previsoes": previsoes_mensais[12:36]},
            "longo_prazo": {"meses": "37-60", "previsoes": previsoes_mensais[36:60]},
        }

        return {
            "horizonte_total_meses": steps,
            "horizonte_anos": round(steps / 12, 1),
            "modelo": f"SARIMAX{self.order}x{self.seasonal_order}",
            "n_features": len(self._feature_names),
            "previsoes_mensais": previsoes_mensais,
            "previsoes_anuais": previsoes_anuais,
            "por_horizonte": horizontes,
            "nota": (
                "Curto prazo (1-12m): maior confiança, exógenas operacionais dominam. "
                "Médio prazo (13-36m): macro e safra ganham peso, IC se abre. "
                "Longo prazo (37-60m): tendência estrutural, IC amplo — usar com cautela."
            ),
        }

    def decompose_drivers(self) -> List[Dict[str, Any]]:
        """Importância relativa de cada variável exógena."""
        if self._results is None or not self._feature_names:
            return []

        try:
            params = self._results.params
            importances = []

            for i, feat in enumerate(self._feature_names):
                param_name = f"x{i+1}" if f"x{i+1}" in params.index else feat
                if param_name in params.index:
                    coef = abs(float(params[param_name]))
                else:
                    matching = [p for p in params.index if feat in str(p)]
                    coef = abs(float(params[matching[0]])) if matching else 0

                importances.append({"feature": feat, "coeficiente": round(coef, 6)})

            total = sum(i["coeficiente"] for i in importances) or 1
            for item in importances:
                item["importancia_pct"] = round(item["coeficiente"] / total * 100, 1)

            return sorted(importances, key=lambda x: -x["importancia_pct"])
        except Exception as e:
            logger.warning("driver_decomposition_error: %s", e)
            return []

    def backtest(
        self,
        df: pd.DataFrame,
        target: str = "tonelagem",
        exog_cols: Optional[List[str]] = None,
        test_months: int = 12,
    ) -> Dict[str, Any]:
        """
        Walk-forward backtesting nos últimos N meses.

        Também testa horizonte de 24 e 36 meses se dados suficientes.
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        min_train = 36
        if len(df) < min_train + test_months:
            return {"error": f"Dados insuficientes (precisa {min_train + test_months}, tem {len(df)})"}

        y = df[target].dropna()
        max_features = max(1, (len(y) - test_months) // MAX_EXOG_RATIO)

        if exog_cols is None:
            exog_cols = self._stepwise_select(
                df.iloc[:-test_months], target, max_features
            )
        exog_cols = exog_cols[:max_features]

        # Testa múltiplos horizontes
        horizontes_teste = [12]
        if len(y) >= min_train + 24:
            horizontes_teste.append(24)
        if len(y) >= min_train + 36:
            horizontes_teste.append(36)

        resultados_horizonte = {}
        for h in horizontes_teste:
            if len(y) < min_train + h:
                continue
            t = len(y) - h
            yt, yv = y.iloc[:t], y.iloc[t:t + h]

            ex_tr = df[exog_cols].ffill().fillna(0).iloc[:t] if exog_cols else None
            ex_te = df[exog_cols].ffill().fillna(0).iloc[t:t + h] if exog_cols else None

            try:
                model = SARIMAX(
                    yt, exog=ex_tr,
                    order=self.order, seasonal_order=self.seasonal_order,
                    enforce_stationarity=False, enforce_invertibility=False,
                )
                results = model.fit(disp=False, maxiter=200)
                preds = results.get_forecast(steps=h, exog=ex_te)
                y_pred = preds.predicted_mean

                n = min(len(yv), len(y_pred))
                errors = np.abs(yv.values[:n] - y_pred.values[:n])
                pct_errors = errors / np.maximum(np.abs(yv.values[:n]), 1)

                comparacao = []
                for i in range(n):
                    period = yv.index[i]
                    comparacao.append({
                        "periodo": period.strftime("%Y-%m") if hasattr(period, "strftime") else str(period),
                        "real": round(float(yv.iloc[i]), 0),
                        "previsto": round(max(0, float(y_pred.iloc[i])), 0),
                        "erro_pct": round(float(pct_errors[i]) * 100, 1),
                    })

                resultados_horizonte[f"{h}m"] = {
                    "horizonte_meses": h,
                    "mae": round(float(np.mean(errors)), 0),
                    "mape_pct": round(float(np.mean(pct_errors)) * 100, 1),
                    "rmse": round(float(np.sqrt(np.mean(errors**2))), 0),
                    "comparacao": comparacao,
                }

                # MAPE por ano dentro do horizonte
                if h >= 24:
                    for year_offset in range(h // 12):
                        start = year_offset * 12
                        end = min(start + 12, n)
                        if end > start:
                            year_errors = pct_errors[start:end]
                            resultados_horizonte[f"{h}m"][f"mape_ano_{year_offset + 1}"] = round(
                                float(np.mean(year_errors)) * 100, 1
                            )

            except Exception as e:
                resultados_horizonte[f"{h}m"] = {"error": str(e)[:200]}

        return {
            "n_features": len(exog_cols),
            "features_used": exog_cols,
            "regra_parcimonia": f"max {max_features} vars",
            "horizontes": resultados_horizonte,
        }

    # ── Seleção de features ─────────────────────────────────────────

    def _stepwise_select(
        self,
        df: pd.DataFrame,
        target: str,
        max_features: int,
    ) -> List[str]:
        """
        Forward stepwise por AIC com penalidade mínima de 2 pontos.

        Só adiciona feature se AIC cai pelo menos 2 pontos.
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        candidates = [
            c for c in numeric_cols
            if c != target
            and "ano" not in c
            and "mes_num" not in c
            and c != "trimestre"
            and c != "atracoes"
        ]

        if not candidates:
            return []

        y = df[target].dropna()

        # Baseline: sem exógenas
        try:
            m = SARIMAX(y, order=self.order, seasonal_order=self.seasonal_order,
                        enforce_stationarity=False, enforce_invertibility=False)
            best_aic = m.fit(disp=False, maxiter=100).aic
        except Exception:
            return []

        selected: List[str] = []

        for _ in range(min(max_features, len(candidates))):
            best_feat = None
            for feat in candidates:
                if feat in selected:
                    continue
                test_cols = selected + [feat]
                try:
                    exog = df.loc[y.index, test_cols].ffill().fillna(0)
                    m = SARIMAX(y, exog=exog, order=self.order,
                                seasonal_order=self.seasonal_order,
                                enforce_stationarity=False, enforce_invertibility=False)
                    aic = m.fit(disp=False, maxiter=100).aic
                    if aic < best_aic - 2:  # Penalidade mínima
                        best_aic = aic
                        best_feat = feat
                except Exception:
                    continue

            if best_feat:
                selected.append(best_feat)
            else:
                break

        return selected

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _aggregate_by_year(previsoes: List[Dict]) -> List[Dict[str, Any]]:
        """Agrega previsões mensais por ano."""
        by_year: Dict[int, List[Dict]] = {}
        for p in previsoes:
            ano = p.get("ano", 0)
            if ano not in by_year:
                by_year[ano] = []
            by_year[ano].append(p)

        anuais = []
        for ano in sorted(by_year):
            items = by_year[ano]
            total = sum(p["tonelagem_prevista"] for p in items)
            anuais.append({
                "ano": ano,
                "meses_previstos": len(items),
                "tonelagem_anual": round(total, 0),
                "tonelagem_media_mensal": round(total / len(items), 0),
                "ic_95_inferior": round(sum(p.get("ic_95_inferior", 0) for p in items), 0),
                "ic_95_superior": round(sum(p.get("ic_95_superior", 0) for p in items), 0),
            })

        return anuais
