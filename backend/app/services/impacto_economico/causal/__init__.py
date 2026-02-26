"""Engine de inferência causal — DiD, IV, Panel IV, SCM (interface).

Portado de new_impacto/src/causal e adaptado para uso como
biblioteca interna do backend SaaS.

Todos os resultados são serializáveis (sem DataFrames crus na saída
de alto nível) graças ao helper :mod:`serialize`.

Fluxo típico::

    from app.services.impacto_economico.causal.prep import build_did_panel
    from app.services.impacto_economico.causal.did import run_did_with_diagnostics
    from app.services.impacto_economico.causal.serialize import serialize_causal_result

    panel = build_did_panel(df, treated_ids=["3304557"], post_year=2015)
    result = run_did_with_diagnostics(panel, outcome="pib_log", treatment_year=2015)
    payload = serialize_causal_result(result)  # list[dict] JSON-safe

Métodos adicionais:
    :mod:`scm` — Synthetic Control Method (implementação local com SLSQP)
    :mod:`augmented_scm` — Augmented SCM (Ben-Michael et al. 2021, ridge correction)
"""

from app.services.impacto_economico.causal.prep import (
    add_uf_from_municipio,
    build_did_panel,
    aggregate_panel_by_uf_year,
    aggregate_antaq_by_uf_year,
)
from app.services.impacto_economico.causal.did import (
    test_parallel_trends,
    run_did,
    run_placebo_tests,
    donor_sensitivity_analysis,
    run_did_specifications,
    run_did_with_diagnostics,
)
from app.services.impacto_economico.causal.event_study import (
    run_event_study,
)
from app.services.impacto_economico.causal.iv import (
    run_iv_2sls,
    first_stage_diagnostics,
    run_reduced_form,
    test_alternative_instruments,
    run_iv_with_diagnostics,
)
from app.services.impacto_economico.causal.iv_panel import (
    run_panel_iv,
    run_panel_iv_with_diagnostics,
)
from app.services.impacto_economico.causal.comparison import (
    compare_method_results,
    create_comparison_report,
)
from app.services.impacto_economico.causal.serialize import (
    serialize_causal_result,
    dataframe_to_records,
    sanitize_scalars,
)
from app.services.impacto_economico.causal.scm import (
    SCMNotAvailableError,
    run_scm,
    run_scm_with_diagnostics,
)
from app.services.impacto_economico.causal.augmented_scm import (
    AugmentedSCMNotAvailableError,
    run_augmented_scm,
    run_augmented_scm_with_diagnostics,
)
from app.services.impacto_economico.causal.matching import suggest_control_matches

__all__ = [
    # prep
    "add_uf_from_municipio",
    "build_did_panel",
    "aggregate_panel_by_uf_year",
    "aggregate_antaq_by_uf_year",
    # did
    "test_parallel_trends",
    "run_event_study",
    "run_did",
    "run_placebo_tests",
    "donor_sensitivity_analysis",
    "run_did_specifications",
    "run_did_with_diagnostics",
    # iv
    "run_iv_2sls",
    "first_stage_diagnostics",
    "run_reduced_form",
    "test_alternative_instruments",
    "run_iv_with_diagnostics",
    # iv_panel
    "run_panel_iv",
    "run_panel_iv_with_diagnostics",
    # comparison
    "compare_method_results",
    "create_comparison_report",
    # serialize
    "serialize_causal_result",
    "dataframe_to_records",
    "sanitize_scalars",
    # scm
    "SCMNotAvailableError",
    "run_scm",
    "run_scm_with_diagnostics",
    # augmented_scm
    "AugmentedSCMNotAvailableError",
    "run_augmented_scm",
    "run_augmented_scm_with_diagnostics",
    # matching (PR-26)
    "suggest_control_matches",
]
