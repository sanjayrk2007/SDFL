import os
import json
import tempfile

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["API_DASHBOARD_KEY"] = "test-api-key"
os.environ["SETUP_TOKEN"] = "test-setup-token"

import base64
os.environ["COORDINATOR_SECRET"] = base64.b64encode(b"x" * 32).decode()

import pytest
import torch
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


async def test_health_no_auth(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0"
    assert isinstance(data["timestamp"], int)


async def test_clients_requires_auth(client):
    resp = await client.get("/clients")
    assert resp.status_code == 401


async def test_clients_empty(client):
    resp = await client.get("/clients", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_audit_log_empty(client):
    resp = await client.get("/audit-log", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 50
    assert data["entries"] == []


async def test_audit_log_pagination(client, test_db):
    async with test_db() as session:
        for i in range(5):
            await session.execute(
                text(
                    "INSERT INTO audit_events (event_type, round_id, details) "
                    "VALUES (:et, :rid, :det)"
                ),
                {
                    "et": "test_event",
                    "rid": i + 1,
                    "det": json.dumps({"idx": i}),
                },
            )
        await session.commit()

    resp = await client.get(
        "/audit-log?page=1&limit=2", headers=AUTH_HEADERS
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["entries"]) == 2


async def test_rounds_empty(client):
    resp = await client.get("/rounds", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_metrics_dice_empty(client):
    resp = await client.get("/metrics/dice", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_metrics_epsilon_empty(client):
    resp = await client.get("/metrics/epsilon", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_round_not_found(client):
    resp = await client.get("/rounds/999", headers=AUTH_HEADERS)
    assert resp.status_code == 404


async def test_rounds_insert_and_read(client, test_db):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    async with test_db() as session:
        await session.execute(
            text(
                "INSERT INTO round_schedules (round_id, window_seconds, "
                "expiry_timestamp, status) VALUES (:rid, :ws, :et, :st)"
            ),
            {
                "rid": 1,
                "ws": 300,
                "et": now.isoformat(),
                "st": "OPEN",
            },
        )
        await session.commit()

    resp = await client.get("/rounds", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["round_id"] == 1
    assert data[0]["status"] == "OPEN"


async def test_register_endpoint(client, test_db):
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    import platform.coordinator.api as api

    certs_dir = tempfile.mkdtemp()
    api.CA_DIR = certs_dir
    api.CA_CERT_PATH = os.path.join(certs_dir, "ca_cert.pem")
    api.CA_KEY_PATH = os.path.join(certs_dir, "ca_key.pem")
    api._ca_cert = None
    api._ca_key = None

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Hospital"),
                x509.NameAttribute(NameOID.COMMON_NAME, "test.sdfl.local"),
            ])
        )
        .sign(key, hashes.SHA256())
    )
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()

    resp = await client.post(
        "/clients/register",
        json={
            "hospital_name": "Test Hospital Alpha",
            "csr_pem": csr_pem,
            "setup_token": "test-setup-token",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "hospital_id" in data
    assert data["client_certificate_pem"].startswith("-----BEGIN CERTIFICATE-----")
    assert data["ca_certificate_pem"].startswith("-----BEGIN CERTIFICATE-----")


async def test_register_invalid_token(client, test_db):
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    import platform.coordinator.api as api

    certs_dir = tempfile.mkdtemp()
    api.CA_DIR = certs_dir
    api.CA_CERT_PATH = os.path.join(certs_dir, "ca_cert.pem")
    api.CA_KEY_PATH = os.path.join(certs_dir, "ca_key.pem")
    api._ca_cert = None
    api._ca_key = None

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Bad Hospital"),
                x509.NameAttribute(NameOID.COMMON_NAME, "bad.sdfl.local"),
            ])
        )
        .sign(key, hashes.SHA256())
    )
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()

    resp = await client.post(
        "/clients/register",
        json={
            "hospital_name": "Bad Hospital",
            "csr_pem": csr_pem,
            "setup_token": "wrong-token",
        },
    )
    assert resp.status_code == 401


async def test_invalid_api_key(client):
    resp = await client.get(
        "/clients", headers={"X-API-Key": "wrong-key"}
    )
    assert resp.status_code == 401


async def test_round_start(client, test_db):
    resp = await client.post(
        "/rounds/start",
        headers=AUTH_HEADERS,
        json={"window_seconds": 300, "num_rounds": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["round_id"] == 1
    assert data["window_seconds"] == 300
    assert data["status"] == "OPEN"


async def test_rollback_not_found(client, test_db):
    resp = await client.post(
        "/rollback?round_id=999", headers=AUTH_HEADERS
    )
    assert resp.status_code == 404


async def test_full_round_audit_log(client, test_db):
    import json as pyjson
    import time
    import uuid
    from datetime import datetime, timezone

    from e7_temporal import TemporalCheckpointingSecAgg
    from crypto import client_encrypt

    class DummyClientProxy:
        def __init__(self, cid):
            self.cid = cid

    class DummyFitRes:
        def __init__(self, metrics, num_examples=100):
            self.metrics = metrics
            self.num_examples = num_examples

    class DummyClientManager:
        def sample(self, num_clients, min_num_clients=None):
            return [DummyClientProxy(f"c{i}") for i in range(min_num_clients or 3)]

        def num_available(self):
            return 3

    SECRET = b"test_coordinator_secret_key_32bytes"
    audit_path = "test_audit_log_e2e.jsonl"
    if os.path.exists(audit_path):
        os.remove(audit_path)

    round_id = 1
    window = 30

    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5,
        secret_key=SECRET,
        window_seconds=window,
    )
    strategy.AUDIT_LOG_PATH = audit_path

    import flwr as fl
    from e4_dpsgd import get_parameters
    from model import ResUNetPlusPlus
    from e4_dpsgd import fix_model_for_opacus
    test_model = ResUNetPlusPlus()
    fix_model_for_opacus(test_model)
    test_params = fl.common.ndarrays_to_parameters(get_parameters(test_model))

    fit_configs = strategy.configure_fit(round_id, test_params, DummyClientManager())
    cfg = fit_configs[0][1].config

    round_key = bytearray(bytes.fromhex(cfg["round_key_hex"]))
    ct = client_encrypt(torch.ones(10), round_key)
    metrics = {
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": cfg["certificate"],
        "signature": cfg["signature"],
        "key_context_id": cfg["key_context_id"],
    }
    results = [(DummyClientProxy("c0"), DummyFitRes(metrics))]
    strategy.aggregate_fit(round_id, results, [])

    assert os.path.exists(audit_path)
    with open(audit_path) as f:
        lines = [pyjson.loads(line.strip()) for line in f]

    events = [e["event"] for e in lines]
    assert "round_open" in events, f"Missing round_open in {events}"
    assert "round_close" in events, f"Missing round_close in {events}"
    assert "key_destroyed" in events, f"Missing key_destroyed in {events}"

    round_open_idx = events.index("round_open")
    round_close_idx = events.index("round_close")
    key_destroyed_idx = events.index("key_destroyed")
    assert round_open_idx < round_close_idx, "round_open must precede round_close"
    assert round_close_idx < key_destroyed_idx, "round_close must precede key_destroyed"

    async with test_db() as session:
        sql_result = await session.execute(
            text("SELECT event_type, round_id FROM audit_events ORDER BY id")
        )
        db_events = sql_result.fetchall()

    if db_events:
        db_types = [r[0] for r in db_events]
        for et in ("round_open", "round_close", "key_destroyed"):
            assert et in db_types, f"Missing {et} in PostgreSQL audit_events"

    if os.path.exists(audit_path):
        os.remove(audit_path)
