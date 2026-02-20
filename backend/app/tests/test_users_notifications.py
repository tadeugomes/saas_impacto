"""Testes para endpoint de preferências de notificação."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI

from .http_test_client import make_sync_asgi_client


TENANT_ID = uuid.uuid4()
USER_ID = uuid.uuid4()


def _make_client():
    import app.api.v1.users as router_module
    from app.api.deps import get_current_user
    from app.db.base import get_db

    test_app = FastAPI()
    test_app.include_router(router_module.router)

    mock_user = MagicMock()
    mock_user.id = USER_ID
    mock_user.tenant_id = TENANT_ID

    async def _mock_db():
        yield AsyncMock()

    async def _mock_user_dep():
        return mock_user

    test_app.dependency_overrides[get_db] = _mock_db
    test_app.dependency_overrides[get_current_user] = _mock_user_dep
    return test_app


class TestUsersNotifications:
    """Cobertura de /users/me/notifications."""

    def _fake_row(self, channel: str, endpoint: str, enabled: bool = True):
        row = MagicMock()
        row.id = uuid.uuid4()
        row.channel = channel
        row.endpoint = endpoint
        row.enabled = enabled
        row.created_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
        row.updated_at = datetime(2026, 2, 2, tzinfo=timezone.utc)
        return row

    def test_list_notifications_returns_list(self):
        service = MagicMock()
        service.list_for_user = AsyncMock(
            return_value=[
                self._fake_row("email", "analista@empresa.com"),
                self._fake_row("webhook", "https://example.com/hook", enabled=False),
            ]
        )
        import app.api.v1.users as router_module

        app = _make_client()
        with patch.object(router_module, "NotificationService", return_value=service):
            client = make_sync_asgi_client(app)
            response = client.get("/users/me/notifications")

        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, list)
        assert len(payload) == 2
        assert payload[0]["channel"] == "email"
        assert payload[1]["enabled"] is False

    def test_update_notifications_calls_service_and_returns_payload(self):
        service = MagicMock()
        service.upsert_many = AsyncMock(
            return_value=[
                self._fake_row("email", "analista@empresa.com"),
                self._fake_row("webhook", "https://example.com/hook"),
            ]
        )
        import app.api.v1.users as router_module

        app = _make_client()
        with patch.object(router_module, "NotificationService", return_value=service):
            client = make_sync_asgi_client(app)
            response = client.put(
                "/users/me/notifications",
                json=[
                    {"channel": "email", "endpoint": "analista@empresa.com", "enabled": True},
                    {"channel": "webhook", "endpoint": "https://example.com/hook", "enabled": True},
                ],
            )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 2
        service.upsert_many.assert_awaited_once()

    def test_update_notifications_validates_channel(self):
        service = MagicMock()
        app = _make_client()
        import app.api.v1.users as router_module

        with patch.object(router_module, "NotificationService", return_value=service):
            client = make_sync_asgi_client(app)
            response = client.put(
                "/users/me/notifications",
                json=[{"channel": "sms", "endpoint": "+55", "enabled": True}],
            )

        assert response.status_code == 422
