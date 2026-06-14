import pytest
from httpx import ASGITransport, AsyncClient

from app.api.health import get_db, get_redis
from app.main import app


class FakeDB:
    async def execute(self, _: object) -> None:
        return None


class FakeRedis:
    def __init__(self, available: bool = True) -> None:
        self.available = available

    async def ping(self) -> bool:
        if not self.available:
            raise ConnectionError
        return True


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": None}


async def test_readiness_success(client: AsyncClient) -> None:
    db = FakeDB()
    redis = FakeRedis()

    async def override_db() -> FakeDB:
        return db

    async def override_redis() -> FakeRedis:
        return redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    try:
        response = await client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["checks"] == {"postgres": "ok", "redis": "ok"}


async def test_readiness_degraded(client: AsyncClient) -> None:
    db = FakeDB()
    redis = FakeRedis(available=False)

    async def override_db() -> FakeDB:
        return db

    async def override_redis() -> FakeRedis:
        return redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    try:
        response = await client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["redis"] == "unavailable"
