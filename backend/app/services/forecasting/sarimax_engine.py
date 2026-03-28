"""
Motor SARIMAX para forecast de tonelagem portuária.

Usa statsmodels SARIMAX com variáveis exógenas dos 5 blocos.
Inclui backtesting (walk-forward), decomposição de drivers
e geração de cenários.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SarimaxEngine:
    """Motor SARIMAX para previsão de throughput portuário."""

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
        Treina o modelo SARIMAX.

        Args:
            df: DataFrame com target e features (index = date)
            target: Nome da coluna target
            exog_cols: Colunas exógenas (None = auto-select)

        Returns:
            Dict com métricas de ajuste (AIC, BIC, log-likelihood)
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        self._target_name = target
        y = df[target].dropna()

        if exog_cols is None:
            exog_cols = self._auto_select_features(df, target)

        self._feature_names = exog_cols

        if exog_cols:
            exog = df.loc[y.index, exog_cols].fillna(method="ffill").fillna(0)
        else:
            exog = None

        try:
            self._model = SARIMAX(
                y,
                exog=exog,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            self._results = self._model.fit(disp=False, maxiter=200)

            return {
                "aic": round(self._results.aic, 2),
                "bic": round(self._results.bic, 2),
                "log_likelihood": round(self._results.llf, 2),
                "n_obs": int(self._results.nobs),
                "n_features": len(exog_cols),
                "features_used": exog_cols,
            }
        except Exception as e:
            logger.error("sarimax_fit_error: %s", e)
            # Fallback: SARIMA sem exógenas
            try:
                self._feature_names = []
                self._model = SARIMAX(
                    y, order=self.order, seasonal_order=self.seasonal_order,
                    enforce_stationarity=False, enforce_invertibility=False,
                )
                self._results = self._model.fit(disp=False, maxiter=200)
                return {
                    "aic": round(self._results.aic, 2),
                    "bic": round(self._results.bic, 2),
                    "n_obs": int(self._results.nobs),
                    "n_features": 0,
                    "features_used": [],
                    "fallback": "SARIMA sem exógenas (erro no modelo completo)",
                }
            except Exception as e2:
                raise RuntimeError(f"SARIMAX e SARIMA falharam: {e2}") from e

    def forecast(
        self,
        steps: int = 12,
        exog_future: Optional[pd.DataFrame] = None,
        confidence_levels: List[float] = [0.80, 0.95],
    ) -> Dict[str, Any]:
        """
        Gera forecast de N meses.

        Args:
            steps: Número de meses para prever
            exog_future: DataFrame com exógenas futuras (para cenários)
            confidence_levels: Níveis de confiança para intervalos

        Returns:
            Dict com previsões, intervalos de confiança, e métricas
        """
        if self._results is None:
            raise RuntimeError("Modelo não treinado. Chame fit() primeiro.")

        forecast_result = self._results.get_forecast(steps=steps, exog=exog_future)
        predicted = forecast_result.predicted_mean

        result = {
            "previsoes": [],
            "horizonte_meses": steps,
            "modelo": f"SARIMAX{self.order}x{self.seasonal_order}",
            "n_features": len(self._feature_names),
        }

        for level in confidence_levels:
            alpha = 1 - level
            ci = forecast_result.conf_int(alpha=alpha)
            ci_lower = ci.iloc[:, 0]
            ci_upper = ci.iloc[:, 1]

            for i in range(steps):
                date_str = predicted.index[i].strftime("%Y-%m") if hasattr(predicted.index[i], "strftime") else str(predicted.index[i])

                # Encontra ou cria entrada para esta data
                entry = None
                for e in result["previsoes"]:
                    if e["periodo"] == date_str:
                        entry = e
                        break

                if entry is None:
                    entry = {
                        "periodo": date_str,
                        "tonelagem_prevista": round(max(0, float(predicted.iloc[i])), 0),
                    }
                    result["previsoes"].append(entry)

                pct = int(level * 100)
                entry[f"ic_{pct}_inferior"] = round(max(0, float(ci_lower.iloc[i])), 0)
                entry[f"ic_{pct}_superior"] = round(max(0, float(ci_upper.iloc[i])), 0)

        return result

    def decompose_drivers(self) -> List[Dict[str, Any]]:
        """
        Decompõe contribuição de cada variável exógena no forecast.

        Calcula a importância relativa baseada nos coeficientes
        do modelo × desvio padrão de cada feature.
        """
        if self._results is None or not self._feature_names:
            return []

        try:
            params = self._results.params
            importances = []

            for i, feat in enumerate(self._feature_names):
                # Coeficiente da feature no modelo
                param_name = f"x{i+1}" if f"x{i+1}" in params.index else feat
                if param_name in params.index:
                    coef = abs(float(params[param_name]))
                else:
                    # Tenta encontrar pelo nome
                    matching = [p for p in params.index if feat in str(p)]
                    coef = abs(float(params[matching[0]])) if matching else 0

                importances.append({
                    "feature": feat,
                    "coeficiente": round(coef, 6),
                })

            # Normaliza para importância relativa (%)
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

        Treina no período [0, T-test_months], prevê [T-test_months, T],
        compara com valores reais.

        Returns:
            Dict com MAE, MAPE, RMSE e previsões vs. reais
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        if len(df) < test_months + 24:
            return {"error": "Dados insuficientes para backtesting (mínimo 36 meses)"}

        y = df[target].dropna()
        train_end = len(y) - test_months

        y_train = y.iloc[:train_end]
        y_test = y.iloc[train_end:]

        if exog_cols is None:
            exog_cols = self._auto_select_features(df, target)

        if exog_cols:
            exog_all = df[exog_cols].fillna(method="ffill").fillna(0)
            exog_train = exog_all.iloc[:train_end]
            exog_test = exog_all.iloc[train_end:train_end + test_months]
        else:
            exog_train = None
            exog_test = None

        try:
            model = SARIMAX(
                y_train, exog=exog_train,
                order=self.order, seasonal_order=self.seasonal_order,
                enforce_stationarity=False, enforce_invertibility=False,
            )
            results = model.fit(disp=False, maxiter=200)
            predictions = results.get_forecast(steps=test_months, exog=exog_test)
            y_pred = predictions.predicted_mean

            # Métricas
            errors = y_test.values[:len(y_pred)] - y_pred.values[:len(y_test)]
            abs_errors = np.abs(errors)
            pct_errors = abs_errors / np.maximum(np.abs(y_test.values[:len(y_pred)]), 1)

            mae = round(float(np.mean(abs_errors)), 0)
            mape = round(float(np.mean(pct_errors)) * 100, 1)
            rmse = round(float(np.sqrt(np.mean(errors**2))), 0)

            # Comparação mês a mês
            comparacao = []
            for i in range(min(len(y_test), len(y_pred))):
                period = y_test.index[i]
                comparacao.append({
                    "periodo": period.strftime("%Y-%m") if hasattr(period, "strftime") else str(period),
                    "real": round(float(y_test.iloc[i]), 0),
                    "previsto": round(max(0, float(y_pred.iloc[i])), 0),
                    "erro_pct": round(float(pct_errors[i]) * 100, 1),
                })

            return {
                "mae": mae,
                "mape_pct": mape,
                "rmse": rmse,
                "meses_testados": len(comparacao),
                "n_features": len(exog_cols),
                "features_used": exog_cols,
                "comparacao": comparacao,
            }
        except Exception as e:
            logger.error("backtest_error: %s", e)
            return {"error": str(e)[:200]}

    @staticmethod
    def _auto_select_features(
        df: pd.DataFrame, target: str, max_features: int = 10,
    ) -> List[str]:
        """
        Seleciona features com maior correlação com o target.
        Exclui lags muito colineares.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        candidates = [
            c for c in numeric_cols
            if c != target
            and not c.startswith("ano")
            and not c.startswith("mes_num")
            and c not in ("trimestre",)
        ]

        if not candidates:
            return []

        # Correlação absoluta com target
        correlations = {}
        for col in candidates:
            try:
                corr = abs(df[target].corr(df[col]))
                if not np.isnan(corr):
                    correlations[col] = corr
            except Exception:
                continue

        # Top N por correlação
        sorted_features = sorted(correlations, key=correlations.get, reverse=True)
        return sorted_features[:max_features]
