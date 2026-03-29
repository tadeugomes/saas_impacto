"""
Teste do pipeline completo de forecasting (Módulo 11).

Exercita o fluxo real do sistema:
  1. FeatureBuilder.build_panel() com os 5 blocos de variáveis:
     - Bloco 1: Histórico (lags, MA, sazonalidade) via BigQuery/ANTAQ
     - Bloco 2: Macro (câmbio PTAX, IBC-Br, Selic, IPCA) via BACEN
     - Bloco 3: Operação (navios, espera, calado) via BigQuery/ANTAQ
     - Bloco 4: Safra (CONAB)
     - Bloco 5: Clima (precipitação INMET, ONI/NOAA, nível rio ANA)
  2. SarimaxEngine.fit() com exog_priority (exógenas reais primeiro)
  3. ScenarioEngine para projeção base/otimista/pessimista
  4. Backtest walk-forward 12 meses
  5. Decomposição padronizada de drivers

Uso:
    cd /caminho/para/saas_impacto
    python test_forecasting.py
    python test_forecasting.py --porto "Paranaguá" --inicio 2015 --fim 2024
"""

import os
import sys
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Caminho base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

# Insere backend no path para imports internos
sys.path.insert(0, BACKEND_DIR)


def load_env() -> Dict[str, str]:
    """Lê variáveis do .env do backend."""
    env_path = os.path.join(BACKEND_DIR, ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


def setup_environment():
    """Configura variáveis de ambiente a partir do .env."""
    env = load_env()
    for k, v in env.items():
        if k not in os.environ:
            os.environ[k] = v
    return env


def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_blocks_status(status: Dict[str, str]):
    """Mostra status de cada bloco de variáveis."""
    labels = {
        "macro": "Bloco 2 (Macro: BACEN)",
        "operacao": "Bloco 3 (Operação: ANTAQ)",
        "safra": "Bloco 4 (Safra: CONAB)",
        "clima": "Bloco 5 (Clima: INMET/NOAA/ANA)",
    }
    for key, label in labels.items():
        s = status.get(key, "nao_executado")
        marker = "OK" if s == "ok" else "SEM DADOS"
        print(f"  {label}: {marker}")


def print_feature_blocks(blocks: Dict[str, List[str]]):
    """Lista features de cada bloco."""
    order = ["historico", "macro", "operacao", "safra", "clima"]
    labels = {
        "historico": "Bloco 1 (Histórico)",
        "macro": "Bloco 2 (Macro)",
        "operacao": "Bloco 3 (Operação)",
        "safra": "Bloco 4 (Safra)",
        "clima": "Bloco 5 (Clima)",
    }
    for key in order:
        feats = blocks.get(key, [])
        label = labels.get(key, key)
        if feats:
            print(f"\n  {label} ({len(feats)} features):")
            for f in feats:
                print(f"    - {f}")
        else:
            print(f"\n  {label}: nenhuma feature")


async def test_full_pipeline(
    id_instalacao: str,
    ano_inicio: int,
    ano_fim: int,
):
    """Executa o pipeline completo de forecasting."""

    from app.services.forecasting.feature_builder import FeatureBuilder
    from app.services.forecasting.sarimax_engine import SarimaxEngine
    from app.services.forecasting.scenario_engine import ScenarioEngine

    # ── 1. FeatureBuilder: monta painel com 5 blocos ──────────────
    print_section(f"1. FEATURE BUILDER ({id_instalacao}, {ano_inicio}-{ano_fim})")

    builder = FeatureBuilder()
    df = await builder.build_panel(
        id_instalacao=id_instalacao,
        id_municipio=None,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
    )

    if df.empty or len(df) < 24:
        print(f"\nERRO: dados insuficientes ({len(df)} meses, mínimo 24). Encerrando.")
        return

    print(f"\nPeríodo: {df.index.min().strftime('%Y-%m')} a {df.index.max().strftime('%Y-%m')}")
    print(f"Observações: {len(df)} meses")
    print(f"Total de features: {len(builder.feature_names)}")
    print(f"  Exógenas reais: {len(builder.exogenous_features)}")
    print(f"  Derivadas do target: {len(builder.derived_features)}")

    print(f"\nStatus dos blocos:")
    print_blocks_status(builder.blocks_status)

    print(f"\nFeatures por bloco:")
    print_feature_blocks(builder.feature_blocks)

    # Estatísticas do target
    print(f"\nTonelagem mensal:")
    print(f"  Média:  {df['tonelagem'].mean():>14,.0f} t")
    print(f"  Mínima: {df['tonelagem'].min():>14,.0f} t ({df['tonelagem'].idxmin().strftime('%Y-%m')})")
    print(f"  Máxima: {df['tonelagem'].max():>14,.0f} t ({df['tonelagem'].idxmax().strftime('%Y-%m')})")

    # Verifica missings nas exógenas
    exog_cols = builder.exogenous_features
    if exog_cols:
        print(f"\nMissings em exógenas reais:")
        for col in exog_cols:
            if col in df.columns:
                n_miss = df[col].isna().sum()
                pct = n_miss / len(df) * 100
                print(f"  {col}: {n_miss}/{len(df)} ({pct:.0f}%)")

    # ── 2. SarimaxEngine: ajuste com prioridade de exógenas ───────
    print_section("2. AJUSTE SARIMAX (exógenas reais priorizadas)")

    engine = SarimaxEngine()
    exog_priority = builder.exogenous_features or None

    logger.info("Ajustando SARIMAX com stepwise AIC...")
    if exog_priority:
        logger.info("Exógenas priorizadas: %s", exog_priority)

    fit_info = engine.fit(df, target="tonelagem", exog_priority=exog_priority)

    print(f"\nOrdem: SARIMAX{engine.order}x{engine.seasonal_order}")
    print(f"AIC:  {fit_info['aic']}")
    print(f"BIC:  {fit_info.get('bic', 'N/A')}")
    print(f"Observações: {fit_info['n_obs']}")
    print(f"Regra de parcimônia: {fit_info['regra_parcimonia']}")
    print(f"Features selecionadas ({fit_info['n_features']}):")

    selected = fit_info["features_used"]
    for feat in selected:
        tipo = builder.classify_feature(feat)
        print(f"  - {feat} [{tipo}]")

    if exog_priority:
        sel_set = set(selected)
        exog_selecionadas = [f for f in exog_priority if f in sel_set]
        print(f"\nExógenas reais no modelo: {len(exog_selecionadas)}/{len(exog_priority)}")
        if not exog_selecionadas:
            print("  AVISO: nenhuma exógena real selecionada pelo stepwise.")
            print("  O modelo ficou restrito a features derivadas do target.")

    if "fallback" in fit_info:
        print(f"Fallback: {fit_info['fallback']}")

    # ── 3. Forecast 60 meses via ScenarioEngine ──────────────────
    print_section("3. FORECAST 60 MESES (cenário base)")

    exog_future = None
    if engine._feature_names:
        try:
            scenario_gen = ScenarioEngine(engine._feature_names)
            scenarios = scenario_gen.generate_exog_scenarios(df, steps=60)
            exog_future = scenarios.get("base")
            if exog_future is not None:
                print(f"ScenarioEngine: cenário base gerado ({len(exog_future)} meses)")
            else:
                print("ScenarioEngine: cenário base vazio, usando fallback")
        except Exception as e:
            print(f"ScenarioEngine: erro ({e}), usando fallback hold-last-value")

    forecast = engine.forecast(steps=60, exog_future=exog_future)

    print(f"\nModelo: {forecast['modelo']}")
    print(f"\n{'Ano':<8} {'Meses':>5} {'Tonelagem anual':>18} {'IC 95% Inf':>15} {'IC 95% Sup':>15}")
    print("-" * 65)
    for ano in forecast["previsoes_anuais"]:
        meses = ano.get("meses_previstos", 12)
        parcial = " *" if meses < 12 else ""
        print(
            f"{ano['ano']:<8} "
            f"{meses:>5} "
            f"{ano['tonelagem_anual']:>18,.0f} "
            f"{ano['ic_95_inferior']:>15,.0f} "
            f"{ano['ic_95_superior']:>15,.0f}{parcial}"
        )
    print("  (* ano parcial, não incluído no CAGR)")

    print(f"\nPrimeiros 6 meses previstos:")
    for m in forecast["previsoes_mensais"][:6]:
        print(
            f"  {m['periodo']}: {m['tonelagem_prevista']:>12,.0f} t  "
            f"[IC95: {m['ic_95_inferior']:,.0f} .. {m['ic_95_superior']:,.0f}]"
        )

    # ── 4. Cenários (base/otimista/pessimista) ────────────────────
    print_section("4. CENÁRIOS (base / otimista / pessimista)")

    if engine._feature_names:
        try:
            scenario_gen = ScenarioEngine(engine._feature_names)
            exog_scenarios = scenario_gen.generate_exog_scenarios(df, steps=60)

            forecasts_cenarios = {}
            for name, exog_fut in exog_scenarios.items():
                forecasts_cenarios[name] = engine.forecast(steps=60, exog_future=exog_fut)

            result_cenarios = scenario_gen.format_scenarios_response(forecasts_cenarios, df)

            if "cenarios" in result_cenarios:
                for cenario_data in result_cenarios["cenarios"]:
                    cenario_nome = cenario_data.get("cenario", "?")
                    anuais = cenario_data.get("previsoes_anuais", [])
                    cagr = cenario_data.get("cagr_pct")
                    if anuais:
                        # Filtra anos completos para display principal
                        completos = [a for a in anuais if a.get("meses_previstos", 12) == 12]
                        if completos:
                            primeiro = completos[0]
                            ultimo = completos[-1]
                        else:
                            primeiro = anuais[0]
                            ultimo = anuais[-1]
                        cagr_str = f"  CAGR={cagr}%" if cagr is not None else ""
                        print(
                            f"\n  {cenario_nome.upper()}: "
                            f"{primeiro['ano']} = {primeiro['tonelagem_anual']:,.0f} t  ...  "
                            f"{ultimo['ano']} = {ultimo['tonelagem_anual']:,.0f} t{cagr_str}"
                        )
                        # Mostra anos parciais separadamente
                        parciais = [a for a in anuais if a.get("meses_previstos", 12) < 12]
                        for p in parciais:
                            print(
                                f"    ({p['ano']}: {p['tonelagem_anual']:,.0f} t "
                                f"- parcial, {p['meses_previstos']} meses)"
                            )
            else:
                print("\nResposta de cenários sem chave 'cenarios'.")
                print(f"Chaves retornadas: {list(result_cenarios.keys())}")

        except Exception as e:
            print(f"\nErro ao gerar cenários: {e}")
    else:
        print("\nSem exógenas no modelo, cenários não aplicáveis.")

    # ── 5. Decomposição de drivers ─────────────────────────────────
    print_section("5. DECOMPOSIÇÃO DE DRIVERS (coeficiente padronizado)")

    drivers = engine.decompose_drivers()

    if drivers:
        print(f"\n{'Feature':<35} {'|Coef| x Std':>14} {'Importância':>13}")
        print("-" * 65)
        for d in drivers:
            tipo = builder.classify_feature(d["feature"])
            tag = " [EXOG]" if tipo == "exogena" else ""
            print(
                f"{d['feature']:<35} "
                f"{d['importancia_padronizada']:>14.4f} "
                f"{d['importancia_pct']:>12.1f}%{tag}"
            )

        # Resumo por tipo
        exog_pct = sum(
            d["importancia_pct"] for d in drivers
            if builder.classify_feature(d["feature"]) == "exogena"
        )
        deriv_pct = sum(
            d["importancia_pct"] for d in drivers
            if builder.classify_feature(d["feature"]) == "derivada"
        )
        print(f"\n  Exógenas reais: {exog_pct:.1f}% da importância total")
        print(f"  Derivadas do target: {deriv_pct:.1f}% da importância total")
    else:
        print("\nSem exógenas selecionadas. Modelo SARIMA puro (sem drivers).")

    # ── 6. Backtest walk-forward ───────────────────────────────────
    print_section("6. BACKTESTING WALK-FORWARD (12 meses)")

    if len(df) >= 36:
        logger.info("Executando backtest walk-forward...")
        backtest = engine.backtest(
            df, target="tonelagem", test_months=12,
            exog_priority=exog_priority,
        )

        if "error" in backtest:
            print(f"\nErro: {backtest['error']}")
        else:
            print(f"\nFeatures usadas: {backtest.get('features_used', [])}")
            for h_name, h_result in backtest.get("horizontes", {}).items():
                if "error" in h_result:
                    print(f"\n  Horizonte {h_name}: erro ({h_result['error'][:80]})")
                    continue
                print(f"\n  Horizonte {h_name}:")
                print(f"    MAE:  {h_result['mae']:>12,.0f} t")
                print(f"    MAPE: {h_result['mape_pct']:>11.1f}%")
                print(f"    RMSE: {h_result['rmse']:>12,.0f} t")

                comparacao = h_result.get("comparacao", [])
                if comparacao:
                    print(f"    Últimos 3 meses:")
                    for c in comparacao[-3:]:
                        print(
                            f"      {c['periodo']}: real={c['real']:>12,.0f}  "
                            f"previsto={c['previsto']:>12,.0f}  "
                            f"erro={c['erro_pct']:>5.1f}%"
                        )
    else:
        print(f"\nDados insuficientes para backtest ({len(df)} meses, mínimo 36).")

    # ── 7. Interpretação de negócio ──────────────────────────────
    print_section("7. INTERPRETAÇÃO DE NEGÓCIO")

    try:
        from app.services.forecasting.forecast_interpreter import create_interpreter
        interpreter = create_interpreter(id_instalacao, df, target="tonelagem")
        interp = interpreter.interpret_all(
            backtest=backtest if len(df) >= 36 else None,
            drivers=drivers,
        )

        # MAPE
        mape_interp = interp.get("mape", {})
        if mape_interp.get("disponivel"):
            print(f"\n  Qualidade: {mape_interp['qualidade']}")
            print(f"  {mape_interp['texto']}")
            print(f"  {mape_interp['impacto_operacional']}")

            # Degradação por horizonte
            deg = mape_interp.get("degradacao_por_horizonte", {})
            pontos = deg.get("por_horizonte", [])
            if pontos:
                print(f"\n  Degradação do MAPE:")
                for p in pontos:
                    print(f"    {p['horizonte']}: MAPE {p['mape_pct']:.1f}% (~{p['erro_medio_mensal_ton']:,.0f} t/mês)")
                por_ano = deg.get("por_ano", [])
                if por_ano:
                    print(f"\n  MAPE por ano (backtest 36m):")
                    for pa in por_ano:
                        print(f"    Ano {pa['ano']}: MAPE {pa['mape_pct']:.1f}%")
                if deg.get("mape_estimado_ano4"):
                    print(f"    Ano 4: ~{deg['mape_estimado_ano4']:.1f}% (estimado)")
                    print(f"    Ano 5: ~{deg['mape_estimado_ano5']:.1f}% (estimado)")

            # Confiança por horizonte
            conf = mape_interp.get("confianca_por_horizonte", {})
            faixas = conf.get("faixas", [])
            if faixas:
                print(f"\n  Confiança por horizonte:")
                for fx in faixas:
                    validado = "validado" if fx["validado"] else "extrapolado"
                    print(f"    {fx['periodo']}: {fx['confianca']} ({validado})")

        # Drivers
        drv_interp = interp.get("drivers", {})
        if drv_interp.get("disponivel"):
            print(f"\n  Perfil do porto: {drv_interp['perfil']}")
            print(f"  {drv_interp['texto']}")

        # Resumo executivo
        resumo = interp.get("resumo_executivo", "")
        if resumo:
            print(f"\n  RESUMO EXECUTIVO:")
            # Quebra em linhas de ~80 chars
            words = resumo.split()
            line = "    "
            for w in words:
                if len(line) + len(w) + 1 > 80:
                    print(line)
                    line = "    " + w
                else:
                    line += " " + w if line.strip() else "    " + w
            if line.strip():
                print(line)

    except Exception as e:
        print(f"\n  Erro na interpretação: {e}")
        import traceback
        traceback.print_exc()

    # ── 8. Resumo ──────────────────────────────────────────────────
    print_section("RESUMO")

    n_blocos_ok = sum(1 for v in builder.blocks_status.values() if v == "ok")
    n_blocos_total = len(builder.blocks_status)

    print(f"Porto:          {id_instalacao}")
    print(f"Período:        {ano_inicio}-{ano_fim} ({len(df)} meses)")
    print(f"Blocos ativos:  {n_blocos_ok}/{n_blocos_total}")
    print(f"Features total: {len(builder.feature_names)}")
    print(f"  Exógenas:     {len(builder.exogenous_features)}")
    print(f"  Derivadas:    {len(builder.derived_features)}")
    print(f"Selecionadas:   {fit_info['n_features']}")

    if selected:
        exog_sel = [f for f in selected if builder.classify_feature(f) == "exogena"]
        deriv_sel = [f for f in selected if builder.classify_feature(f) == "derivada"]
        print(f"  Exógenas sel.: {len(exog_sel)} ({', '.join(exog_sel) if exog_sel else 'nenhuma'})")
        print(f"  Derivadas sel.: {len(deriv_sel)} ({', '.join(deriv_sel) if deriv_sel else 'nenhuma'})")

    print(f"Modelo:         SARIMAX{engine.order}x{engine.seasonal_order}")
    print(f"AIC:            {fit_info['aic']}")
    print(f"Horário:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(
        description="Teste do pipeline completo de forecasting (Módulo 11)"
    )
    parser.add_argument("--porto", default="Santos", help="Nome do porto (padrão: Santos)")
    parser.add_argument("--inicio", type=int, default=2014, help="Ano de início (padrão: 2014)")
    parser.add_argument("--fim", type=int, default=datetime.now().year, help="Ano de fim (padrão: ano corrente)")
    args = parser.parse_args()

    env = setup_environment()

    print_section(f"TESTE PIPELINE FORECASTING (Módulo 11)")
    print(f"Porto:        {args.porto}")
    print(f"Período:      {args.inicio}-{args.fim}")
    print(f"Projeto GCP:  {env.get('GCP_PROJECT_ID', 'nao_definido')}")
    print(f"Credenciais:  {env.get('GOOGLE_APPLICATION_CREDENTIALS', 'nao_definido')}")
    print(f"Backend dir:  {BACKEND_DIR}")

    asyncio.run(test_full_pipeline(args.porto, args.inicio, args.fim))


if __name__ == "__main__":
    main()
