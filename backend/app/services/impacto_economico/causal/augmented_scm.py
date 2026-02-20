"""Interface Augmented Synthetic Control Method (ASCM) — Módulo Impacto Econômico.

Status: NÃO IMPLEMENTADO (MVP honesto).
======================================

O Augmented SCM combina o controle sintético clássico com regularização
por regressão (Ben-Michael, Feller & Rothstein, 2021), corrigindo o
viés de imbalance pré-tratamento do SCM tradicional.

O módulo ``synthetic_augmented.py`` que implementa o ASCM ainda não está
disponível nesta versão do ``saas_impacto``. Ele está sendo portado do
repositório ``new_impacto`` (``run_augmented_scm_with_placebo.py``).

Para habilitar quando o módulo estiver disponível
-------------------------------------------------
1. Porte ``new_impacto/src/causal/synthetic_augmented.py`` para:
   ``backend/app/services/impacto_economico/causal/synthetic_augmented.py``
2. Substitua as funções stub deste módulo pelas chamadas reais.
3. Configure a feature flag no ``.env``::

       ENABLE_AUGMENTED_SCM=true

Interface de retorno esperada (compatível com ``comparison.py``)
----------------------------------------------------------------
.. code-block:: python

    {
        "augmented_result": {
            "post_att":     float,   # ATT médio pós (ASCM)
            "pre_rmspe":    float,   # RMSPE pré (com bias correction)
            "post_rmspe":   float,
            "w_optimal":    list,    # Pesos sintéticos augmentados
            "ridge_lambda": float,   # Parâmetro de regularização selecionado
        },
        "base_scm_result": {         # SCM clássico para comparação
            "post_att":    float,
            "pre_rmspe":   float,
        },
        "placebo_test": {
            "p_value":           float,
            "in_time_placebos":  list[dict],   # placebos temporais
            "in_space_placebos": list[dict],   # placebos espaciais
        },
        "event_study":  list[dict],
        "warnings":     list[str],
    }

Referência
----------
Ben-Michael, E., Feller, A., & Rothstein, J. (2021). The Augmented
Synthetic Control Method. *Journal of the American Statistical
Association*, 116(536), 1789–1803.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


# ── Exceção pública ────────────────────────────────────────────────────────


class AugmentedSCMNotAvailableError(NotImplementedError):
    """Augmented Synthetic Control Method não disponível nesta versão.

    Levantada quando a feature flag ``ENABLE_AUGMENTED_SCM`` está
    desabilitada (padrão) ou quando o módulo ``synthetic_augmented.py``
    ainda não foi portado do repositório ``new_impacto``.
    """

    _MESSAGE = (
        "O método 'augmented_scm' (Augmented Synthetic Control) ainda não está "
        "disponível nesta versão do SaaS Impacto Portuário.\n"
        "\n"
        "O módulo synthetic_augmented.py está sendo portado do repositório "
        "new_impacto (run_augmented_scm_with_placebo.py). Quando disponível:\n"
        "  1. Copie new_impacto/src/causal/synthetic_augmented.py para "
        "backend/app/services/impacto_economico/causal/\n"
        "  2. Configure ENABLE_AUGMENTED_SCM=true no .env\n"
        "\n"
        "Métodos disponíveis agora: 'did', 'iv', 'panel_iv', 'event_study', 'compare'.\n"
        "Para Synthetic Control clássico (quando disponível): método 'scm'."
    )

    def __init__(self) -> None:
        super().__init__(self._MESSAGE)


# ── Interface pública (stubs) ──────────────────────────────────────────────


def run_augmented_scm(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    ridge_lambda: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa Augmented SCM (sem diagnósticos completos).

    **NÃO IMPLEMENTADO** — levanta :exc:`AugmentedSCMNotAvailableError`.

    Parameters
    ----------
    df:
        Painel municipio-ano preparado via ``build_did_panel``.
    outcome:
        Coluna de outcome a ser modelada.
    treatment_year:
        Ano T₀ do tratamento.
    controls:
        Covariáveis para o matching sintético augmentado.
    ridge_lambda:
        Parâmetro de regularização Ridge. ``None`` → seleção automática
        por cross-validation pré-tratamento.

    Raises
    ------
    AugmentedSCMNotAvailableError
        Sempre, até que o módulo seja portado e ``ENABLE_AUGMENTED_SCM=true``.
    """
    raise AugmentedSCMNotAvailableError()


def run_augmented_scm_with_diagnostics(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    ridge_lambda: float | None = None,
    n_placebos: int = 50,
    run_in_time_placebo: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa Augmented SCM com diagnósticos completos.

    **NÃO IMPLEMENTADO** — levanta :exc:`AugmentedSCMNotAvailableError`.

    Parameters
    ----------
    df:
        Painel municipio-ano preparado via ``build_did_panel``.
    outcome:
        Coluna de outcome.
    treatment_year:
        Ano T₀ do tratamento.
    controls:
        Covariáveis para matching sintético.
    ridge_lambda:
        Regularização Ridge (``None`` = auto via CV pré-período).
    n_placebos:
        Número de unidades placebo para o teste in-space.
    run_in_time_placebo:
        Se ``True``, executa também placebos temporais (in-time).

    Returns
    -------
    dict compatível com ``compare_method_results(scm_result=...)``::

        {
            "augmented_result": {"post_att": float, "pre_rmspe": float, ...},
            "base_scm_result":  {"post_att": float, "pre_rmspe": float},
            "placebo_test":     {"p_value": float, ...},
            "event_study":      [{"year": int, "effect": float}, ...],
            "warnings":         [...],
        }

    Raises
    ------
    AugmentedSCMNotAvailableError
        Sempre, até que o módulo seja portado e ``ENABLE_AUGMENTED_SCM=true``.
    """
    raise AugmentedSCMNotAvailableError()
