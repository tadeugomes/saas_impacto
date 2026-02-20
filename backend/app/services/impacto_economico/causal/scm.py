"""Interface Synthetic Control Method (SCM) — Módulo Impacto Econômico.

Status: NÃO IMPLEMENTADO (MVP honesto).
======================================

O módulo ``synthetic_control.py`` que implementa o SCM ainda não está
disponível nesta versão do repositório ``saas_impacto``. Ele está sendo
portado do repositório ``new_impacto`` (scripts ``run_scm_*.py``).

Para habilitar quando o módulo estiver disponível
-------------------------------------------------
1. Porte ``new_impacto/src/causal/synthetic_control.py`` para:
   ``backend/app/services/impacto_economico/causal/synthetic_control.py``
2. Substitua as funções stub deste módulo pelas chamadas reais.
3. Configure a feature flag no ``.env``::

       ENABLE_SCM=true

Interface de retorno esperada (compatível com ``comparison.py``)
----------------------------------------------------------------
.. code-block:: python

    {
        "base_result": {
            "post_att":    float,   # ATT médio pós-tratamento
            "pre_rmspe":   float,   # RMSPE no período pré (qualidade do fit)
            "post_rmspe":  float,   # RMSPE no período pós
            "w_optimal":   list,    # Pesos ótimos do controle sintético
            "donor_units": list,    # IDs das unidades doadoras
        },
        "placebo_test": {
            "p_value":          float,      # p-value por rank dos placebos
            "in_space_placebos": list[dict] # placebo por unidade doadora
        },
        "event_study":  list[dict],         # efeito por ano relativo ao tratamento
        "warnings":     list[str],
    }

Referência alternativa (``augmented_scm.py``)
---------------------------------------------
Para o Augmented SCM que combina SCM com regressão (Ben-Michael et al., 2021),
veja :mod:`app.services.impacto_economico.causal.augmented_scm`.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


# ── Exceção pública ────────────────────────────────────────────────────────


class SCMNotAvailableError(NotImplementedError):
    """Synthetic Control Method não disponível nesta versão.

    Levantada quando a feature flag ``ENABLE_SCM`` está desabilitada
    (padrão) ou quando o módulo ``synthetic_control.py`` ainda não foi
    portado do repositório ``new_impacto``.
    """

    _MESSAGE = (
        "O método 'scm' (Synthetic Control Method) ainda não está disponível "
        "nesta versão do SaaS Impacto Portuário.\n"
        "\n"
        "O módulo synthetic_control.py está sendo portado do repositório "
        "new_impacto. Quando disponível:\n"
        "  1. Copie new_impacto/src/causal/synthetic_control.py para "
        "backend/app/services/impacto_economico/causal/\n"
        "  2. Configure ENABLE_SCM=true no .env\n"
        "\n"
        "Métodos disponíveis agora: 'did', 'iv', 'panel_iv', 'event_study', 'compare'."
    )

    def __init__(self) -> None:
        super().__init__(self._MESSAGE)


# ── Interface pública (stubs) ──────────────────────────────────────────────


def run_scm(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa Synthetic Control Method (sem diagnósticos).

    **NÃO IMPLEMENTADO** — levanta :exc:`SCMNotAvailableError`.

    Parameters
    ----------
    df:
        Painel municipio-ano com colunas ``municipio_id``, ``ano``,
        ``treat`` (dummy), e as colunas de outcome/controles.
    outcome:
        Nome da coluna de outcome.
    treatment_year:
        Ano de início do tratamento (T₀).
    controls:
        Covariáveis para matching sintético (além do outcome defasado).

    Raises
    ------
    SCMNotAvailableError
        Sempre, até que o módulo seja portado e ``ENABLE_SCM=true``.
    """
    raise SCMNotAvailableError()


def run_scm_with_diagnostics(
    df: pd.DataFrame,
    outcome: str,
    treatment_year: int,
    controls: list[str] | None = None,
    n_placebos: int = 50,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa SCM com diagnósticos completos (placebo, event study).

    **NÃO IMPLEMENTADO** — levanta :exc:`SCMNotAvailableError`.

    Parameters
    ----------
    df:
        Painel municipio-ano preparado via ``build_did_panel``.
    outcome:
        Coluna de outcome a ser modelada.
    treatment_year:
        Ano T₀ do tratamento.
    controls:
        Covariáveis adicionais para o matching sintético.
    n_placebos:
        Número de unidades placebo no teste in-space.

    Returns
    -------
    dict compatível com ``compare_method_results(scm_result=...)``::

        {
            "base_result":  {"post_att": float, "pre_rmspe": float, ...},
            "placebo_test": {"p_value": float, "in_space_placebos": [...]},
            "event_study":  [{"year": int, "effect": float}, ...],
            "warnings":     [...],
        }

    Raises
    ------
    SCMNotAvailableError
        Sempre, até que o módulo seja portado e ``ENABLE_SCM=true``.
    """
    raise SCMNotAvailableError()
