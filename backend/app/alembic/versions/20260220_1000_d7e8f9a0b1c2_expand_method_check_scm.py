"""Expande CHECK constraint method para incluir scm e augmented_scm.

Revision ID: d7e8f9a0b1c2
Revises: c8f3a1d92b47
Create Date: 2026-02-20 10:00:00.000000

Contexto
--------
O PR-07 adiciona "scm" e "augmented_scm" como métodos válidos na tabela
``economic_impact_analyses``. Ambos requerem feature flag habilitada no
.env para serem executados (ENABLE_SCM / ENABLE_AUGMENTED_SCM).

A constraint original aceitava apenas:
    did | iv | panel_iv | event_study | compare

A nova constraint adiciona:
    scm | augmented_scm

Reversibilidade
--------------
O downgrade remove os valores scm/augmented_scm da constraint.
Rows com method IN ('scm', 'augmented_scm') devem ser removidas antes
do downgrade; do contrário, o ALTER TABLE falhará por violação de constraint.
"""
from __future__ import annotations

from alembic import op

# ── Metadados Alembic ──────────────────────────────────────────────────────
revision = "d7e8f9a0b1c2"
down_revision = "c8f3a1d92b47"
branch_labels = None
depends_on = None

# ── Constantes ─────────────────────────────────────────────────────────────
TABLE_NAME = "economic_impact_analyses"
CONSTRAINT_NAME = "ck_economic_impact_analyses_method"

_METHODS_V1 = "('did', 'iv', 'panel_iv', 'event_study', 'compare')"
_METHODS_V2 = "('did', 'iv', 'panel_iv', 'event_study', 'compare', 'scm', 'augmented_scm')"

_DROP_CONSTRAINT = (
    f"ALTER TABLE {TABLE_NAME} DROP CONSTRAINT {CONSTRAINT_NAME}"
)
_ADD_CONSTRAINT_V2 = (
    f"ALTER TABLE {TABLE_NAME} ADD CONSTRAINT {CONSTRAINT_NAME} "
    f"CHECK (method IN {_METHODS_V2})"
)
_ADD_CONSTRAINT_V1 = (
    f"ALTER TABLE {TABLE_NAME} ADD CONSTRAINT {CONSTRAINT_NAME} "
    f"CHECK (method IN {_METHODS_V1})"
)


def upgrade() -> None:
    """Expande a constraint para aceitar 'scm' e 'augmented_scm'."""
    op.execute(_DROP_CONSTRAINT)
    op.execute(_ADD_CONSTRAINT_V2)


def downgrade() -> None:
    """Reverte para a constraint original (apenas métodos estáveis).

    Aviso: falhará se houver rows com method='scm' ou method='augmented_scm'.
    Execute antes::

        DELETE FROM economic_impact_analyses
        WHERE method IN ('scm', 'augmented_scm');
    """
    op.execute(_DROP_CONSTRAINT)
    op.execute(_ADD_CONSTRAINT_V1)
