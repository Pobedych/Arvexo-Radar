from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.deps import get_session
from app.main import app


def test_health_ok() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_ok_when_database_responds() -> None:
    session = AsyncMock()

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        response = TestClient(app).get("/api/v1/ready")
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}
    session.execute.assert_awaited_once()


def test_ready_returns_503_when_database_is_unavailable() -> None:
    session = AsyncMock()
    session.execute.side_effect = RuntimeError("database unavailable")

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        response = TestClient(app).get("/api/v1/ready")
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
