import os
import base64

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


async def test_unregistered_fingerprint_rejected(client, test_db):
    import platform.coordinator.api as api
    import tempfile
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization

    certs_dir = tempfile.mkdtemp()
    api.CA_DIR = certs_dir
    api.CA_CERT_PATH = os.path.join(certs_dir, "ca_cert.pem")
    api.CA_KEY_PATH = os.path.join(certs_dir, "ca_key.pem")
    api._ca_cert = None
    api._ca_key = None

    legit_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    legit_csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Legit Hospital"),
            x509.NameAttribute(NameOID.COMMON_NAME, "legit.sdfl.local"),
        ]))
        .sign(legit_key, hashes.SHA256())
    )
    legit_csr_pem = legit_csr.public_bytes(serialization.Encoding.PEM).decode()

    resp1 = await client.post("/clients/register", json={
        "hospital_name": "Legit Hospital",
        "csr_pem": legit_csr_pem,
        "setup_token": "test-setup-token",
    })
    assert resp1.status_code == 200
    legit_cert_pem = resp1.json()["client_certificate_pem"]
    legit_fingerprint = api._cert_fingerprint(legit_cert_pem)

    async with test_db() as session:
        result = await session.execute(
            text("SELECT certificate_fingerprint FROM registered_clients")
        )
        stored = result.scalar()
    assert stored == legit_fingerprint

    sybil_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    sybil_csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Sybil Corp"),
            x509.NameAttribute(NameOID.COMMON_NAME, "sybil.sdfl.local"),
        ]))
        .sign(sybil_key, hashes.SHA256())
    )
    sybil_csr_pem = sybil_csr.public_bytes(serialization.Encoding.PEM).decode()

    resp2 = await client.post("/clients/register", json={
        "hospital_name": "Sybil Corp",
        "csr_pem": sybil_csr_pem,
        "setup_token": "test-setup-token",
    })
    assert resp2.status_code == 200
    sybil_cert_pem = resp2.json()["client_certificate_pem"]
    sybil_fingerprint = api._cert_fingerprint(sybil_cert_pem)

    assert legit_fingerprint != sybil_fingerprint

    async with test_db() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM registered_clients")
        )
        count = result.scalar()
    assert count == 2

    async with test_db() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM registered_clients WHERE is_active = 1")
        )
        active_count = result.scalar()
    assert active_count == 2
