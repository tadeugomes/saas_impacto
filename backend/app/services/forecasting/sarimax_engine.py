"""
Motor SARIMAX para forecast de tonelagem portuária.

Horizonte: até 60 meses (5 anos), dividido em 3 faixas:
  - Curto prazo (1-12m): SARIMAX com exógenas operacionais + clima
  - Médio prazo (13-36m): SARIMAX com exógenas macro + safra
  - Longo prazo (37-60m): Tendência estrutural + sazonalidade

Seleção parcimoniosa: max 3-4 exógenas (regra 1:25 obs/feature).
Stepwise AIC com penalidade mínima de 2 pontos.

Prioridade de features:
  1. Exógenas reais (BACEN, INMET, CONAB, etc.) — projetáveis via cenários
  2. Derivadas do target (lags, MA) — usadas como fallback quando
     exógenas reais são insuficientes
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
        self._training_df: Optional[pd.DataFrame] = None

    def fit(
        self,
        df: pd.DataFrame,
        target: str = "tonelagem",
        exog_cols: Optional[List[str]] = None,
        exog_priority: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Treina o modelo SARIMAX com seleção parcimoniosa de features.

        Prioriza exógenas reais (projetáveis) sobre derivadas do target
        quando `exog_priority` é fornecido. Isso garante que o modelo
        use variáveis que podem ser projetadas via cenários para
        forecast out-of-sample.

        Args:
            df: Painel de features com target e exógenas.
            target: Nome da coluna target (default: 'tonelagem').
            exog_cols: Lista fixa de exógenas (sobrescreve seleção automática).
            exog_priority: Lista de features prioritárias (exógenas reais).
                Se fornecido, essas features são testadas primeiro no stepwise.
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        self._target_name = target
        self._training_df = df.copy()
        y = df[target].dropna()

        # Limite de features baseado no tamanho da amostra
        max_features = max(1, len(y) // MAX_EXOG_RATIO)

        if exog_cols is None:
            exog_cols = self._stepwise_select(
                df, target, max_features, exog_priority=exog_priority,
            )

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

            # Classifica features selecionadas
            n_exog_real = 0
            n_derivadas = 0
            for col in exog_cols:
                is_derived = any(col.startswith(p) for p in (
                    "ton_lag_", "ton_ma_", "ton_mom", "ton_yoy",
                    "sin_mes", "cos_mes", "mes_num", "trimestre",
                    "atracoes", "ano",
                ))
                if is_derived:
                    n_derivadas += 1
                else:
                    n_exog_real += 1

            return {
                "aic": round(self._results.aic, 2),
                "bic": round(self._results.bic, 2),
                "n_obs": int(self._results.nobs),
                "n_features": len(exog_cols),
                "n_exogenas_reais": n_exog_real,
                "n_derivadas_target": n_derivadas,
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
                    "n_exogenas_reais": 0,
                    "n_derivadas_target": 0,
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

        Se exog_future não for fornecido e o modelo usa features:
          - Para exógenas reais: gera projeção via cenário base (ScenarioEngine)
          - Fallback: hold-last-value do conjunto de treino

        Returns:
            Dict com previsões anuais e mensais + IC + horizonte
        """
        if self._results is None:
            raise RuntimeError("Modelo não treinado. Chame fit() primeiro.")

        # Gera exog_future se necessário
        if exog_future is None and self._feature_names:
            exog_future = self._build_exog_future(steps)

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

        # Método de projeção das exógenas
        metodo_exog = "cenario_base"
        if exog_future is None:
            metodo_exog = "sem_exogenas"
        elif isinstance(exog_future, np.ndarray):
            metodo_exog = "hold_last_value"

        return {
            "horizonte_total_meses": steps,
            "horizonte_anos": round(steps / 12, 1),
            "modelo": f"SARIMAX{self.order}x{self.seasonal_order}",
            "n_features": len(self._feature_names),
            "metodo_projecao_exogenas": metodo_exog,
            "previsoes_mensais": previsoes_mensais,
            "previsoes_anuais": previsoes_anuais,
            "por_horizonte": horizontes,
        }

    def decompose_drivers(self) -> List[Dict[str, Any]]:
        """
        Importância relativa de cada variável exógena.

        Usa coeficiente padronizado: |coef| * std(feature).
        Isso corrige o viés de escala que fazia features percentuais
        (ton_mom, ton_yoy) dominarem sobre features em toneladas.
        """
        if self._results is None or not self._feature_names:
            return []

        try:
            params = self._results.params
            training_exog = self._training_df

            importances = []
            for i, feat in enumerate(self._feature_names):
                # Encontra o coeficiente no modelo
                param_name = f"x{i+1}" if f"x{i+1}" in params.index else feat
                if param_name in params.index:
                    coef = float(params[param_name])
                else:
                    matching = [p for p in params.index if feat in str(p)]
                    coef = float(params[matching[0]]) if matching else 0

                # Desvio-padrão da feature no treino
                std = 1.0
                if training_exog is not None and feat in training_exog.columns:
                    s = training_exog[feat].dropna().std()
                    if s > 0:
                        std = float(s)

                # Importância padronizada = |coef| × std
                standardized = abs(coef) * std

                importances.append({
                    "feature": feat,
                    "coeficiente_raw": round(coef, 6),
                    "std_feature": round(std, 4),
                    "importancia_padronizada": round(standardized, 2),
                })

            total = sum(i["importancia_padronizada"] for i in importances) or 1
            for item in importances:
                item["importancia_pct"] = round(
                    item["importancia_padronizada"] / total * 100, 1
                )

            return sorted(importances, key=lambda x: -x["importancia_pct"])
        except Exception as e:
            logger.warning("driver_decomposition_error: %s", e)
            return []

    def backtest(
        self,
        df: pd.DataFrame,
        target: str = "tonelagem",
        exog_cols: Optional[List[str]] = None,
        exog_priority: Optional[List[str]] = None,
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
                df.iloc[:-test_months], target, max_features,
                exog_priority=exog_priority,
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
        exog_priority: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Forward stepwise por AIC em 2 estágios.

        O problema de um stepwise único é que features derivadas do target
        (lags, MA) capturam autocorrelação direta e sempre vencem exógenas
        reais em AIC individual. Mas derivadas não podem ser projetadas para
        horizonte longo (exigem hold-last-value), enquanto exógenas reais
        são projetáveis via cenários.

        Estágio 1: Seleciona até ceil(max_features * 0.6) entre as exógenas
            reais (BACEN, INMET, CONAB, operação). Penalidade AIC reduzida
            (melhoria > 0 basta) para não perder variáveis com efeito
            moderado mas projetável.

        Estágio 2: Preenche os slots restantes com qualquer candidata
            (derivadas ou exógenas que sobraram). Penalidade AIC padrão
            (melhoria > 2 pontos).

        Se nenhuma exógena real passar no estágio 1 (blocos sem dados ou
        features sem poder preditivo), todos os slots vão para o estágio 2.
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        import math

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        candidates_all = [
            c for c in numeric_cols
            if c != target
            and "ano" not in c
            and "mes_num" not in c
            and c != "trimestre"
            and c != "atracoes"
        ]

        if not candidates_all:
            return []

        y = df[target].dropna()

        # Baseline: SARIMA puro
        try:
            m = SARIMAX(y, order=self.order, seasonal_order=self.seasonal_order,
                        enforce_stationarity=False, enforce_invertibility=False)
            baseline_aic = m.fit(disp=False, maxiter=100).aic
        except Exception:
            return []

        selected: List[str] = []
        current_aic = baseline_aic

        # Separa candidatas
        if exog_priority:
            priority_set = set(exog_priority)
            exog_candidates = [c for c in candidates_all if c in priority_set]
            derived_candidates = [c for c in candidates_all if c not in priority_set]
        else:
            exog_candidates = []
            derived_candidates = candidates_all

        # ── Estágio 1: exógenas reais (slots reservados) ──────────
        slots_exog = math.ceil(max_features * 0.6) if exog_candidates else 0
        slots_exog = min(slots_exog, len(exog_candidates))

        if exog_candidates:
            logger.info(
                "stepwise estágio 1: %d exógenas candidatas, %d slots reservados",
                len(exog_candidates), slots_exog,
            )

        for _ in range(slots_exog):
            best_feat = None
            best_aic_candidate = current_aic
            for feat in exog_candidates:
                if feat in selected:
                    continue
                test_cols = selected + [feat]
                try:
                    exog = df.loc[y.index, test_cols].ffill().fillna(0)
                    # Descarta features com variância zero (constantes)
                    if exog[feat].std() < 1e-10:
                        continue
                    m = SARIMAX(y, exog=exog, order=self.order,
                                seasonal_order=self.seasonal_order,
                                enforce_stationarity=False, enforce_invertibility=False)
                    aic = m.fit(disp=False, maxiter=100).aic
                    # Penalidade reduzida: qualquer melhoria > 0 basta
                    if aic < best_aic_candidate:
                        best_aic_candidate = aic
                        best_feat = feat
                except Exception:
                    continue

            if best_feat:
                selected.append(best_feat)
                current_aic = best_aic_candidate
                logger.info(
                    "stepwise estágio 1: +%s (AIC %.2f → %.2f)",
                    best_feat, current_aic + (current_aic - best_aic_candidate),
                    current_aic,
                )
            else:
                break

        n_exog_selected = len(selected)
        slots_remaining = max_features - n_exog_selected

        logger.info(
            "stepwise: estágio 1 selecionou %d exógenas, %d slots para estágio 2",
            n_exog_selected, slots_remaining,
        )

        # ── Estágio 2: derivadas + exógenas restantes ─────────────
        stage2_candidates = derived_candidates + [
            c for c in exog_candidates if c not in selected
        ]

        for _ in range(min(slots_remaining, len(stage2_candidates))):
            best_feat = None
            best_aic_candidate = current_aic
            for feat in stage2_candidates:
                if feat in selected:
                    continue
                test_cols = selected + [feat]
                try:
                    exog = df.loc[y.index, test_cols].ffill().fillna(0)
                    if exog[feat].std() < 1e-10:
                        continue
                    m = SARIMAX(y, exog=exog, order=self.order,
                                seasonal_order=self.seasonal_order,
                                enforce_stationarity=False, enforce_invertibility=False)
                    aic = m.fit(disp=False, maxiter=100).aic
                    # Penalidade padrão: melhoria > 2 pontos
                    if aic < best_aic_candidate - 2:
                        best_aic_candidate = aic
                        best_feat = feat
                except Exception:
                    continue

            if best_feat:
                selected.append(best_feat)
                current_aic = best_aic_candidate
            else:
                break

        logger.info(
            "stepwise final: %d features (%d exógenas + %d derivadas), AIC=%.2f",
            len(selected), n_exog_selected, len(selected) - n_exog_selected,
            current_aic,
        )

        return selected

    # ── Projeção de exógenas ────────────────────────────────────────

    def _build_exog_future(self, steps: int) -> Any:
        """
        Gera projeção de exógenas futuras para forecast.

        Tenta usar ScenarioEngine (cenário base) quando exógenas reais
        estão presentes. Fallback: hold-last-value para features derivadas.
        """
        if self._training_df is None:
            # Fallback: repete a última linha do treino
            last_exog = self._results.model.exog[-1:, :]
            return np.tile(last_exog, (steps, 1))

        try:
            from app.services.forecasting.scenario_engine import ScenarioEngine

            scenario_gen = ScenarioEngine(self._feature_names)
            scenarios = scenario_gen.generate_exog_scenarios(
                self._training_df, steps=steps
            )
            base_exog = scenarios.get("base")

            if base_exog is not None and not base_exog.empty:
                logger.info(
                    "forecast: exog_future via cenário base para %d features",
                    len(self._feature_names),
                )
                return base_exog

        except Exception as e:
            logger.warning("forecast: ScenarioEngine falhou (%s), usando hold-last-value", e)

        # Fallback: hold-last-value
        last_exog = self._results.model.exog[-1:, :]
        logger.debug(
            "forecast: exog_future via hold-last-value para %d features",
            len(self._feature_names),
        )
        return np.tile(last_exog, (steps, 1))

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
