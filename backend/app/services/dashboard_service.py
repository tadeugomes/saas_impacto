"""Serviços agregados para dashboard administrativo."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.audit_log import AuditLog
from app.db.models.economic_impact_analysis import EconomicImpactAnalysis
from app.db.models.user import User
from app.schemas.admin import TenantUsageIndicatorsItem, TenantUsageResponse

settings = get_settings()


class DashboardService:
    """Agrega métricas administrativas por tenant."""

    async def usage(self, db: AsyncSession, tenant_id, rate_limit_cap: int | None = None) -> TenantUsageResponse:
        now = datetime.now(timezone.utc)
        last_30d = now - timedelta(days=30)
        last_7d = now - timedelta(days=7)

        analises_stmt = select(EconomicImpactAnalysis).where(
            EconomicImpactAnalysis.tenant_id == tenant_id
        )
        analises_rows = list((await db.execute(analises_stmt)).scalars().all())

        total_analises = len(analises_rows)
        analises_sucesso = sum(1 for row in analises_rows if row.status == "success")
        analises_falha = sum(1 for row in analises_rows if row.status == "failed")

        active_users_30d_stmt = select(func.count()).where(
            User.tenant_id == tenant_id,
            User.last_login.is_not(None),
            User.last_login >= last_30d,
        )
        active_users_7d_stmt = select(func.count()).where(
            User.tenant_id == tenant_id,
            User.last_login.is_not(None),
            User.last_login >= last_7d,
        )
        users_30d = int((await db.execute(active_users_30d_stmt)).scalar_one_or_none() or 0)
        users_7d = int((await db.execute(active_users_7d_stmt)).scalar_one_or_none() or 0)

        audit_stmt = (
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id, AuditLog.created_at >= last_30d)
        )
        logs = list((await db.execute(audit_stmt)).scalars().all())
        bq_bytes_last_30d = sum(int(log.bytes_processed or 0) for log in logs)

        indicator_counts: dict[str, int] = {}
        for log in logs:
            codigo = None
            if log.details:
                codigo = log.details.get("codigo_indicador")
                if not codigo:
                    codigo = log.details.get("code")
            if not codigo:
                continue
            indicator_counts[str(codigo)] = indicator_counts.get(str(codigo), 0) + 1

        top_indicators = sorted(
            (
                TenantUsageIndicatorsItem(
                    codigo=codigo,
                    nome=codigo,
                    acessos=count,
                )
                for codigo, count in indicator_counts.items()
            ),
            key=lambda item: item.acessos,
            reverse=True,
        )[:10]

        taxa_rate_limit = None
        if rate_limit_cap and total_analises:
            taxa_rate_limit = min(total_analises / rate_limit_cap, 1.0)

        return TenantUsageResponse(
            total_analises=total_analises,
            analises_sucesso=analises_sucesso,
            analises_falha=analises_falha,
            usuarios_ativos_7d=users_7d,
            usuarios_ativos_30d=users_30d,
            bq_bytes_last_30d=bq_bytes_last_30d,
            taxa_rate_limit=taxa_rate_limit,
            top_indicadores=top_indicators,
        )


def get_dashboard_service() -> DashboardService:
    """Dependency provider."""
    return DashboardService()
