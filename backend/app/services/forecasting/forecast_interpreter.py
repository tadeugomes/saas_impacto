"""
Interpretação de resultados de forecast em linguagem de negócio.

Traduz MAPE, cenários e drivers para texto compreensível por
gestores portuários e analistas sem formação estatística.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Capacidade média por navio Panamax (toneladas)
_PANAMAX_CAPACITY = 60_000


class ForecastInterpreter:
    """Gera interpretações textuais dos resultados do forecast."""

    def __init__(
        self,
        id_instalacao: str,
        media_mensal_ton: float,
        media_anual_ton: float,
    ):
        self.id_instalacao = id_instalacao
        self.media_mensal = media_mensal_ton
        self.media_anual = media_anual_ton

    def interpret_all(
        self,
        backtest: Optional[Dict[str, Any]] = None,
        drivers: Optional[List[Dict[str, Any]]] = None,
        scenarios: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Gera interpretação completa reunindo MAPE, drivers e cenários.

        Returns:
            Dict com chaves: mape, drivers, cenarios, resumo_executivo
        """
        result: Dict[str, Any] = {}

        if backtest:
            result["mape"] = self._interpret_mape(backtest)

        if drivers:
            result["drivers"] = self._interpret_drivers(drivers)

        if scenarios:
            result["cenarios"] = self._interpret_scenarios(scenarios)

        # Resumo executivo combinado
        result["resumo_executivo"] = self._build_executive_summary(result)

        return result

    # ── MAPE ──────────────────────────────────────────────────────────

    def _interpret_mape(self, backtest: Dict[str, Any]) -> Dict[str, Any]:
        """Traduz MAPE em toneladas absolutas, equivalente em navios, e degradação por horizonte."""
        horizontes = backtest.get("horizontes", {})

        # Extrai MAPE de cada horizonte testado
        mape_por_horizonte = {}
        for key in ["12m", "24m", "36m"]:
            h = horizontes.get(key, {})
            if "mape_pct" in h:
                mape_por_horizonte[key] = h["mape_pct"]

        # Extrai MAPE por ano dentro dos horizontes longos (24m, 36m)
        mape_por_ano = {}
        for key in ["24m", "36m"]:
            h = horizontes.get(key, {})
            for year in range(1, 6):
                field = f"mape_ano_{year}"
                if field in h:
                    mape_por_ano[f"ano_{year}"] = h[field]

        # Fallback: tenta formato legado
        mape_12m = mape_por_horizonte.get("12m")
        if mape_12m is None:
            mape_12m = backtest.get("mape_12m") or backtest.get("mape", {}).get("12m")

        if mape_12m is None:
            return {"disponivel": False}

        mape_pct = float(mape_12m)
        erro_mensal_ton = self.media_mensal * (mape_pct / 100)
        erro_anual_ton = self.media_anual * (mape_pct / 100)
        navios_mes = erro_mensal_ton / _PANAMAX_CAPACITY

        # Classificação qualitativa
        if mape_pct <= 5:
            qualidade = "alta"
            qualidade_texto = (
                f"O modelo tem precisão alta para {self.id_instalacao}. "
                f"O erro médio de {mape_pct:.1f}% permite planejamento "
                f"operacional mensal com boa confiabilidade."
            )
        elif mape_pct <= 8:
            qualidade = "adequada"
            qualidade_texto = (
                f"O modelo tem precisão adequada para {self.id_instalacao}. "
                f"O erro de {mape_pct:.1f}% é compatível com planejamento "
                f"tático (3-6 meses) e dimensionamento de capacidade."
            )
        elif mape_pct <= 12:
            qualidade = "moderada"
            qualidade_texto = (
                f"O modelo tem precisão moderada para {self.id_instalacao}. "
                f"O erro de {mape_pct:.1f}% exige margens de segurança "
                f"maiores no planejamento operacional."
            )
        else:
            qualidade = "baixa"
            qualidade_texto = (
                f"O modelo tem precisão baixa para {self.id_instalacao} "
                f"(MAPE {mape_pct:.1f}%). Recomenda-se revisar a "
                f"disponibilidade de dados e features para este porto."
            )

        # Curva de degradação e confiança por horizonte
        degradacao = self._build_degradacao(mape_por_horizonte, mape_por_ano)
        confianca_horizonte = self._build_confianca_horizonte(mape_por_horizonte)

        return {
            "disponivel": True,
            "mape_pct": round(mape_pct, 1),
            "qualidade": qualidade,
            "erro_medio_mensal_ton": round(erro_mensal_ton, 0),
            "erro_medio_anual_ton": round(erro_anual_ton, 0),
            "equivalente_navios_panamax_mes": round(navios_mes, 1),
            "texto": qualidade_texto,
            "impacto_operacional": (
                f"Na prática, a previsão mensal erra em média "
                f"{erro_mensal_ton:,.0f} toneladas (equivalente a "
                f"~{navios_mes:.0f} navios Panamax). "
                f"Em base anual ({self.media_anual / 1e6:,.1f}M t), "
                f"a incerteza é de ±{erro_anual_ton / 1e6:,.1f}M toneladas."
            ),
            "degradacao_por_horizonte": degradacao,
            "confianca_por_horizonte": confianca_horizonte,
            "referencia_mercado": (
                "Modelos de forecast portuário na literatura acadêmica "
                "reportam MAPE entre 5% e 15% para horizontes de 12 meses, "
                "dependendo da diversificação de cargas do porto."
            ),
        }

    def _build_degradacao(
        self,
        mape_por_horizonte: Dict[str, float],
        mape_por_ano: Dict[str, float],
    ) -> Dict[str, Any]:
        """Monta curva de degradação do MAPE com distância temporal."""
        pontos = []
        for key, val in sorted(mape_por_horizonte.items()):
            meses = int(key.replace("m", ""))
            erro_ton = self.media_mensal * (val / 100)
            pontos.append({
                "horizonte": key,
                "meses": meses,
                "mape_pct": val,
                "erro_medio_mensal_ton": round(erro_ton, 0),
            })

        # Adiciona MAPE por ano (do backtest de 36m) para granularidade
        pontos_anuais = []
        for key, val in sorted(mape_por_ano.items()):
            ano = int(key.replace("ano_", ""))
            erro_ton = self.media_mensal * (val / 100)
            pontos_anuais.append({
                "ano": ano,
                "mape_pct": val,
                "erro_medio_mensal_ton": round(erro_ton, 0),
            })

        # Estimativa para anos 4 e 5 por extrapolação linear
        mape_estimado_ano4 = None
        mape_estimado_ano5 = None
        if len(pontos_anuais) >= 2:
            # Taxa de degradação média entre anos consecutivos
            degradacoes = []
            for i in range(1, len(pontos_anuais)):
                diff = pontos_anuais[i]["mape_pct"] - pontos_anuais[i - 1]["mape_pct"]
                degradacoes.append(diff)
            taxa_media = sum(degradacoes) / len(degradacoes)
            ultimo_mape = pontos_anuais[-1]["mape_pct"]
            ultimo_ano = pontos_anuais[-1]["ano"]

            if ultimo_ano <= 3:
                mape_estimado_ano4 = round(ultimo_mape + taxa_media, 1)
                mape_estimado_ano5 = round(ultimo_mape + taxa_media * 2, 1)

        # Texto explicativo
        if pontos:
            primeiro = pontos[0]
            ultimo = pontos[-1]
            texto = (
                f"O erro do modelo cresce com a distância temporal. "
                f"No horizonte de {primeiro['horizonte']}, o MAPE é "
                f"{primeiro['mape_pct']:.1f}%. "
                f"Em {ultimo['horizonte']}, sobe para {ultimo['mape_pct']:.1f}%."
            )
            if mape_estimado_ano5 is not None:
                texto += (
                    f" Por extrapolação, os anos 4 e 5 teriam MAPE estimado "
                    f"de ~{mape_estimado_ano4:.0f}% e ~{mape_estimado_ano5:.0f}%, "
                    f"mas essa estimativa não tem validação empírica."
                )
        else:
            texto = "Dados de degradação por horizonte não disponíveis."

        return {
            "por_horizonte": pontos,
            "por_ano": pontos_anuais,
            "mape_estimado_ano4": mape_estimado_ano4,
            "mape_estimado_ano5": mape_estimado_ano5,
            "texto": texto,
        }

    def _build_confianca_horizonte(
        self, mape_por_horizonte: Dict[str, float],
    ) -> Dict[str, Any]:
        """Gera alerta de confiança para cada faixa do horizonte de 5 anos."""
        tem_36m = "36m" in mape_por_horizonte
        tem_24m = "24m" in mape_por_horizonte

        # Nível de confiança validado vs. extrapolado
        faixas = [
            {
                "periodo": "Ano 1 (meses 1-12)",
                "confianca": "alta",
                "validado": True,
                "texto": (
                    "Validado por backtest walk-forward com dados reais. "
                    "MAPE medido empiricamente."
                ),
            },
            {
                "periodo": "Ano 2 (meses 13-24)",
                "confianca": "alta" if tem_24m else "moderada",
                "validado": tem_24m,
                "texto": (
                    "Validado por backtest de 24 meses com dados reais."
                    if tem_24m else
                    "Série insuficiente para backtest de 24 meses. "
                    "Confiança baseada na extrapolação do MAPE de 12 meses."
                ),
            },
            {
                "periodo": "Ano 3 (meses 25-36)",
                "confianca": "moderada" if tem_36m else "baixa",
                "validado": tem_36m,
                "texto": (
                    "Validado por backtest de 36 meses, mas com treino "
                    "reduzido (7 anos). MAPE medido, com ressalva."
                    if tem_36m else
                    "Série insuficiente para backtest de 36 meses. "
                    "Resultado é extrapolação sem validação empírica."
                ),
            },
            {
                "periodo": "Anos 4-5 (meses 37-60)",
                "confianca": "baixa",
                "validado": False,
                "texto": (
                    "Não há dados suficientes para validar este horizonte. "
                    "A projeção depende dos cenários macroeconômicos e "
                    "climáticos (otimista/base/pessimista). Use o "
                    "intervalo entre cenários como medida de incerteza, "
                    "não a previsão pontual."
                ),
            },
        ]

        texto_resumo = (
            "Os anos 1 a 3 têm validação empírica por backtest. "
            "Os anos 4 e 5 são projeções baseadas nos cenários macro "
            "e climáticos, sem validação histórica possível com a "
            "série atual. Para decisões de longo prazo, o spread "
            "entre cenários otimista e pessimista é a melhor medida "
            "de incerteza nesse horizonte."
        )

        return {
            "faixas": faixas,
            "texto_resumo": texto_resumo,
        }

    # ── Drivers ───────────────────────────────────────────────────────

    def _interpret_drivers(
        self, drivers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Traduz importância dos drivers para linguagem de negócio."""
        if not drivers:
            return {"disponivel": False}

        # Separa exógenas reais de derivadas do target
        exogenas = []
        derivadas = []
        for d in drivers:
            feat = d.get("feature", "")
            if any(p in feat for p in ["ton_lag", "ton_ma", "ton_mom", "ton_yoy"]):
                derivadas.append(d)
            else:
                exogenas.append(d)

        pct_exogenas = sum(d.get("importancia_pct", 0) for d in exogenas)
        pct_derivadas = sum(d.get("importancia_pct", 0) for d in derivadas)

        # Top 3 drivers
        top3 = drivers[:3] if len(drivers) >= 3 else drivers
        top3_nomes = [_feature_label(d["feature"]) for d in top3]
        top3_pcts = [d.get("importancia_pct", 0) for d in top3]

        # Texto interpretativo
        if pct_exogenas > 30:
            perfil = "sensível a fatores externos"
            perfil_texto = (
                f"O throughput de {self.id_instalacao} depende de "
                f"fatores externos ({pct_exogenas:.0f}% da importância do modelo). "
                f"Mudanças em {top3_nomes[0]} e {top3_nomes[1] if len(top3_nomes) > 1 else 'outros fatores'} "
                f"têm impacto direto na previsão. "
                f"Isso torna os cenários otimista/pessimista mais relevantes "
                f"para o planejamento."
            )
        else:
            perfil = "inercial"
            perfil_texto = (
                f"O throughput de {self.id_instalacao} segue padrão "
                f"predominantemente inercial ({pct_derivadas:.0f}% da "
                f"importância vem do histórico do próprio porto). "
                f"A tendência e sazonalidade recentes são os melhores "
                f"preditores. Choques externos têm efeito limitado."
            )

        return {
            "disponivel": True,
            "perfil": perfil,
            "pct_exogenas": round(pct_exogenas, 1),
            "pct_derivadas": round(pct_derivadas, 1),
            "top3": [
                {"nome": n, "importancia_pct": round(p, 1)}
                for n, p in zip(top3_nomes, top3_pcts)
            ],
            "texto": perfil_texto,
        }

    # ── Cenários ──────────────────────────────────────────────────────

    def _interpret_scenarios(
        self, scenarios: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Traduz spread entre cenários para impacto operacional."""
        cenarios_list = scenarios.get("cenarios", [])
        if not cenarios_list:
            return {"disponivel": False}

        # Extrai tonelagem do primeiro e último ano por cenário
        by_name = {}
        for c in cenarios_list:
            nome = c.get("cenario", "")
            anuais = c.get("previsoes_anuais", [])
            if anuais:
                by_name[nome] = {
                    "ano1": anuais[0].get("tonelagem_anual", 0),
                    "ultimo": anuais[-1].get("tonelagem_anual", 0),
                    "cagr": c.get("cagr_pct"),
                    "n_anos": len(anuais),
                }

        if "otimista" not in by_name or "pessimista" not in by_name:
            return {"disponivel": False}

        spread_ano1 = by_name["otimista"]["ano1"] - by_name["pessimista"]["ano1"]
        spread_final = by_name["otimista"]["ultimo"] - by_name["pessimista"]["ultimo"]
        navios_spread_ano1 = spread_ano1 / _PANAMAX_CAPACITY

        # CAGR por cenário
        cagr_otim = by_name["otimista"].get("cagr")
        cagr_pess = by_name["pessimista"].get("cagr")
        cagr_base = by_name.get("base", {}).get("cagr")
        n_anos = by_name["otimista"].get("n_anos", 5)

        texto_cenarios = (
            f"No primeiro ano, a diferença entre cenário otimista e "
            f"pessimista é de {spread_ano1 / 1e6:,.1f}M toneladas "
            f"(~{navios_spread_ano1:,.0f} navios Panamax). "
            f"Ao fim do horizonte de {n_anos} anos, o spread acumulado "
            f"chega a {spread_final / 1e6:,.1f}M toneladas."
        )

        if cagr_base is not None and cagr_otim is not None and cagr_pess is not None:
            texto_cenarios += (
                f" A taxa de crescimento anual composta (CAGR) varia "
                f"de {cagr_pess:+.1f}% (pessimista) a {cagr_otim:+.1f}% "
                f"(otimista), com cenário base em {cagr_base:+.1f}%."
            )

        texto_decisao = (
            "Para decisões de investimento de longo prazo (CAPEX em berços, "
            "dragagem, armazéns), o intervalo entre cenários é mais "
            "relevante que a previsão pontual, porque embute a incerteza "
            "macro e climática que o MAPE de 12 meses não captura."
        )

        return {
            "disponivel": True,
            "spread_ano1_ton": round(spread_ano1, 0),
            "spread_final_ton": round(spread_final, 0),
            "navios_panamax_spread_ano1": round(navios_spread_ano1, 0),
            "cagr_otimista": cagr_otim,
            "cagr_base": cagr_base,
            "cagr_pessimista": cagr_pess,
            "horizonte_anos": n_anos,
            "texto": texto_cenarios,
            "texto_decisao": texto_decisao,
        }

    # ── Resumo executivo ──────────────────────────────────────────────

    def _build_executive_summary(
        self, interpretacoes: Dict[str, Any]
    ) -> str:
        """Monta resumo executivo combinando todas as interpretações."""
        partes = [f"Forecast de throughput para {self.id_instalacao}."]

        mape = interpretacoes.get("mape", {})
        if mape.get("disponivel"):
            partes.append(mape["impacto_operacional"])

        drivers = interpretacoes.get("drivers", {})
        if drivers.get("disponivel"):
            partes.append(drivers["texto"])

        cenarios = interpretacoes.get("cenarios", {})
        if cenarios.get("disponivel"):
            partes.append(cenarios["texto"])
            partes.append(cenarios["texto_decisao"])

        return " ".join(partes)


# ── Helpers ───────────────────────────────────────────────────────────


def _feature_label(feature_name: str) -> str:
    """Traduz nome técnico da feature para rótulo legível."""
    labels = {
        "navios_atendidos": "navios atendidos",
        "tempo_espera_horas": "tempo de espera no porto",
        "tempo_atracacao_horas": "tempo de atracação",
        "ibc_br": "atividade econômica (IBC-Br)",
        "cambio_ptax": "câmbio (PTAX)",
        "selic_meta": "taxa Selic",
        "ipca_mensal": "inflação (IPCA)",
        "precipitacao_acumulada_mm": "precipitação acumulada",
        "oni_index": "índice El Niño (ONI)",
        "safra_soja_mil_ton": "produção de soja",
        "safra_milho_mil_ton": "produção de milho",
        "safra_acucar_mil_ton": "produção de açúcar",
        "safra_cafe_mil_ton": "produção de café",
        "safra_soja_yoy": "variação anual da safra de soja",
        "safra_milho_yoy": "variação anual da safra de milho",
        "ton_lag_1": "tonelagem do mês anterior",
        "ton_lag_2": "tonelagem de 2 meses atrás",
        "ton_lag_3": "tonelagem de 3 meses atrás",
        "ton_lag_12": "tonelagem do mesmo mês do ano anterior",
        "ton_ma_3": "média móvel 3 meses",
        "ton_ma_6": "média móvel 6 meses",
        "ton_ma_12": "média móvel 12 meses",
        "ton_mom": "variação mensal",
        "ton_yoy": "variação anual",
    }
    return labels.get(feature_name, feature_name.replace("_", " "))


def create_interpreter(
    id_instalacao: str,
    df_treino,
    target: str = "tonelagem",
) -> ForecastInterpreter:
    """
    Factory que calcula médias a partir do DataFrame de treino
    e retorna um ForecastInterpreter pronto para uso.
    """
    serie = df_treino[target].dropna()
    media_mensal = float(serie.mean())
    # Usa o último ano completo para média anual
    ultimo_ano = serie.index[-1].year - 1
    anual = serie[serie.index.year == ultimo_ano]
    if len(anual) >= 12:
        media_anual = float(anual.sum())
    else:
        media_anual = media_mensal * 12

    return ForecastInterpreter(
        id_instalacao=id_instalacao,
        media_mensal_ton=media_mensal,
        media_anual_ton=media_anual,
    )
