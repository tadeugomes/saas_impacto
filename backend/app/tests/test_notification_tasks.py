"""Testes da task de notificação de finalização de análise."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from uuid import uuid4
import pytest
from celery.exceptions import Retry

from app.schemas.notification import NotificationPreferenceCreate
from app.services.notification_service import NotificationService


class _Settings:
    notifications_enabled = True
    sendgrid_api_key = None
    sendgrid_from_email = "noreply@tests.local"


class _Analysis:
    """Mock mínimo de EconomicImpactAnalysis."""

    def __init__(self, analysis_id: str, tenant_id: str, user_id: str) -> None:
        self.id = analysis_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.method = "did"
        self.status = "success"


def _mock_analysis_payload(analysis_id: str, tenant_id: str, user_id: str) -> _Analysis:
    return _Analysis(analysis_id=analysis_id, tenant_id=tenant_id, user_id=user_id)


def _make_task_client():
    from app.tasks import notifications

    return notifications


def _httpx_mock_client(post_response: object = None):
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    client.post = AsyncMock(return_value=post_response)
    return client


class TestNotificationService:
    """Valida regras de normalização e deduplicação no CRUD."""

    @pytest.mark.asyncio
    async def test_upsert_many_deduplicates_same_channel(self):
        service = NotificationService(uuid4(), uuid4())
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        payload = [
            NotificationPreferenceCreate(channel="email", endpoint="first@empresa.com", enabled=True),
            NotificationPreferenceCreate(channel="email", endpoint="second@empresa.com", enabled=False),
            NotificationPreferenceCreate(channel="webhook", endpoint="https://example.com/webhook", enabled=True),
        ]

        rows = await service.upsert_many(db, payload)
        assert len(rows) == 2
        assert rows[0].channel == "email"
        assert rows[0].endpoint == "second@empresa.com"


class TestNotificationTask:
    """Validação de comportamento da task de notificações."""

    @pytest.mark.asyncio
    async def test_webhook_notification_is_sent_with_expected_payload(self):
        task_module = _make_task_client()
        analysis_id = "11111111-1111-1111-1111-111111111111"
        tenant_id = "22222222-2222-2222-2222-222222222222"
        user_id = "33333333-3333-3333-3333-333333333333"
        analysis = _mock_analysis_payload(analysis_id, tenant_id, user_id)
        pref = _NotificationPreferenceMock(
            channel="webhook",
            endpoint="https://example.com/hooks/impacto",
            enabled=True,
        )

        session = AsyncMock()
        session.get = AsyncMock(return_value=analysis)
        session.__aenter__.return_value = session
        session.__aexit__.return_value = False

        response = MagicMock()
        response.raise_for_status = MagicMock()
        mock_client = _httpx_mock_client(response)

        with patch("app.tasks.notifications.get_settings", return_value=_Settings()), \
             patch("app.db.base.AsyncSessionLocal", return_value=session), \
             patch("app.services.notification_service.NotificationService") as mock_service_cls, \
             patch("app.tasks.notifications.httpx.AsyncClient", return_value=mock_client):
            service = MagicMock()
            service.list_for_user = AsyncMock(return_value=[pref])
            mock_service_cls.return_value = service

            failures = await task_module._notify_sync(analysis_id, tenant_id)

        assert failures == []
        mock_client.post.assert_awaited_once_with(
            "https://example.com/hooks/impacto",
            json={
                "analysis_id": analysis_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "method": "did",
                "status": "success",
            },
        )

    def test_task_retries_on_delivery_failure(self):
        task_module = _make_task_client()
        with patch("app.tasks.notifications._notify_sync", AsyncMock(side_effect=RuntimeError("falha"))):
            with pytest.raises((Retry, RuntimeError)):
                task_module.notify_analysis_complete.run(
                    "11111111-1111-1111-1111-111111111111",
                    "22222222-2222-2222-2222-222222222222",
                )

    def test_task_returns_done_when_no_failures(self):
        task_module = _make_task_client()
        with patch("app.tasks.notifications._notify_sync", AsyncMock(return_value=[])):
            result = task_module.notify_analysis_complete.run(
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
            )

        assert result == {"analysis_id": "11111111-1111-1111-1111-111111111111", "status": "done"}


class _NotificationPreferenceMock(SimpleNamespace):
    """Estrutura compatível com NotificationPreference para testes."""
