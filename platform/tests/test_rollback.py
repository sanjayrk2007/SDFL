import os
import json
import base64
import tempfile

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["API_DASHBOARD_KEY"] = "test-api-key"
os.environ["SETUP_TOKEN"] = "test-setup-token"
os.environ["COORDINATOR_SECRET"] = base64.b64encode(b"x" * 32).decode()

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from platform.coordinator.api import app
from platform.coordinator.db import get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    engine = create_async_engine(TEST_DB_URL)

    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS registered_clients (
                hospital_id VARCHAR(36) PRIMARY KEY,
                hospital_name VARCHAR(255) NOT NULL,
                certificate_fingerprint VARCHAR(64) UNIQUE NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_versions (
                round_id INTEGER PRIMARY KEY,
                checkpoint_path VARCHAR(512) NOT NULL,
                val_dice REAL NOT NULL,
                val_iou REAL NOT NULL,
                epsilon REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 0
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS round_schedules (
                round_id INTEGER PRIMARY KEY,
                window_seconds INTEGER NOT NULL,
                expiry_timestamp TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL
                    CHECK(status IN ('OPEN','CLOSED','AGGREGATING','COMPLETED')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type VARCHAR(100) NOT NULL,
                round_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        """))

    TestSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _get_db_override():
        async with TestSessionLocal() as session:
            yield session

    import platform.coordinator.api as api
    api.AsyncSessionLocal = TestSessionLocal

    app.dependency_overrides[get_db] = _get_db_override

    yield TestSessionLocal

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
async def client(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


AUTH_HEADERS = {"X-API-Key": "test-api-key"}


@pytest.fixture
def checkpoint_dir():
    path = os.path.join(tempfile.gettempdir(), "sdfl_test_checkpoints", "round_1")
    os.makedirs(path, exist_ok=True)
    model_path = os.path.join(path, "global_model.pth")
    import torch
    torch.save({"dummy": torch.zeros(1)}, model_path)
    yield os.path.dirname(os.path.dirname(path))
    import shutil
    shutil.rmtree(os.path.dirname(path), ignore_errors=True)


async def test_rollback_restores_checkpoint(client, test_db, checkpoint_dir):
    import platform.coordinator.api as api
    original_checkpoint_base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "checkpoints"
    )
    api_checkpoint_dir = os.path.join(
        os.path.dirname(api.__file__), "..", "..", "checkpoints"
    )
    os.makedirs(api_checkpoint_dir, exist_ok=True)

    round_1_dir = os.path.join(api_checkpoint_dir, "round_1")
    os.makedirs(round_1_dir, exist_ok=True)
    import torch
    torch.save({"dummy": torch.zeros(1)}, os.path.join(round_1_dir, "global_model.pth"))

    async with test_db() as session:
        await session.execute(
            text(
                "INSERT INTO model_versions (round_id, checkpoint_path, val_dice, val_iou, epsilon, is_active) "
                "VALUES (:rid, :cp, :vd, :vi, :ep, :act)"
            ),
            {
                "rid": 1,
                "cp": os.path.join(api_checkpoint_dir, "round_1/global_model.pth"),
                "vd": 0.85,
                "vi": 0.75,
                "ep": 1.5,
                "act": False,
            },
        )
        await session.execute(
            text(
                "INSERT INTO model_versions (round_id, checkpoint_path, val_dice, val_iou, epsilon, is_active) "
                "VALUES (:rid, :cp, :vd, :vi, :ep, :act)"
            ),
            {
                "rid": 2,
                "cp": "checkpoints/round_2/global_model.pth",
                "vd": 0.88,
                "vi": 0.78,
                "ep": 2.0,
                "act": True,
            },
        )
        await session.commit()

    resp = await client.post("/rollback?round_id=1", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rolled_back"
    assert data["round"] == 1

    async with test_db() as session:
        result = await session.execute(
            text("SELECT round_id, is_active FROM model_versions ORDER BY round_id")
        )
        versions = result.fetchall()

    version_map = {r[0]: r[1] for r in versions}
    assert version_map[1] is True or version_map[1] == 1
    assert version_map[2] is False or version_map[2] == 0

    async with test_db() as session:
        result = await session.execute(
            text("SELECT event_type, round_id FROM audit_events WHERE event_type = 'model_rollback'")
        )
        rollback_events = result.fetchall()

    assert len(rollback_events) >= 1
    assert rollback_events[0][1] == 1

    import shutil
    if os.path.exists(api_checkpoint_dir):
        shutil.rmtree(api_checkpoint_dir, ignore_errors=True)
