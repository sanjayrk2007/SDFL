import asyncio
import contextlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi import (
    FastAPI, Depends, HTTPException, Header, Query, WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from platform.coordinator.config import get_api_key, get_database_url
from platform.coordinator.db import (
    get_db,
    AsyncSessionLocal,
    RegisteredClient,
    ModelVersion,
    RoundSchedule,
    AuditEvent,
)

# ---- Pydantic schemas ----

class RegisterClientRequest(BaseModel):
    hospital_name: str = Field(..., max_length=255)
    csr_pem: str
    setup_token: str


class RegisterClientResponse(BaseModel):
    hospital_id: uuid.UUID
    client_certificate_pem: str
    ca_certificate_pem: str


class StartRoundRequest(BaseModel):
    window_seconds: int = Field(300, ge=60, le=7200)
    num_rounds: int = Field(1, ge=1, le=50)


class RoundSchema(BaseModel):
    round_id: int
    window_seconds: int
    expiry_timestamp: datetime
    status: str


class AuditLogEntry(BaseModel):
    id: int
    event_type: str
    round_id: Optional[int] = None
    timestamp: datetime
    details: Optional[dict] = None


class AuditLogPagination(BaseModel):
    total: int
    page: int
    limit: int
    entries: list[AuditLogEntry]


# ---- CA certificate management ----

CA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "certs")
CA_CERT_PATH = os.path.join(CA_DIR, "ca_cert.pem")
CA_KEY_PATH = os.path.join(CA_DIR, "ca_key.pem")

_ca_cert = None
_ca_key = None


def _load_or_create_ca():
    global _ca_cert, _ca_key
    if _ca_cert is not None and _ca_key is not None:
        return _ca_cert, _ca_key

    if os.path.exists(CA_CERT_PATH) and os.path.exists(CA_KEY_PATH):
        with open(CA_CERT_PATH, "rb") as f:
            _ca_cert = x509.load_pem_x509_certificate(f.read())
        with open(CA_KEY_PATH, "rb") as f:
            _ca_key = serialization.load_pem_private_key(f.read(), password=None)
    else:
        _ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SDFL"),
            x509.NameAttribute(NameOID.COMMON_NAME, "SDFL Root CA"),
        ])
        _ca_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(_ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(
                datetime.now(timezone.utc).replace(
                    year=datetime.now(timezone.utc).year + 10
                )
            )
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .sign(_ca_key, hashes.SHA256())
        )
        os.makedirs(CA_DIR, exist_ok=True)
        with open(CA_CERT_PATH, "wb") as f:
            f.write(_ca_cert.public_bytes(serialization.Encoding.PEM))
        with open(CA_KEY_PATH, "wb") as f:
            f.write(
                _ca_key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )

    return _ca_cert, _ca_key


def _sign_csr(csr_pem: str):
    ca_cert, ca_key = _load_or_create_ca()
    csr = x509.load_pem_x509_csr(csr_pem.encode())
    cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(
            datetime.now(timezone.utc).replace(
                year=datetime.now(timezone.utc).year + 1
            )
        )
        .sign(ca_key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM).decode()


def _cert_fingerprint(cert_pem: str) -> str:
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    return cert.fingerprint(hashes.SHA256()).hex()


# ---- FastAPI app ----

@contextlib.asynccontextmanager
async def lifespan(application):
    _load_or_create_ca()
    yield


app = FastAPI(title="SDFL Coordinator API", version="1.0", lifespan=lifespan)


def get_setup_token() -> str:
    token = os.getenv("SETUP_TOKEN")
    if not token:
        raise RuntimeError("SETUP_TOKEN environment variable not set")
    return token


async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    expected = get_api_key()
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ---- Endpoints ----

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": int(time.time()), "version": "1.0"}


@app.get("/clients", dependencies=[Depends(verify_api_key)])
async def list_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RegisteredClient).order_by(desc(RegisteredClient.registered_at))
    )
    clients = result.scalars().all()
    return [
        {
            "hospital_id": str(c.hospital_id),
            "hospital_name": c.hospital_name,
            "registered_at": c.registered_at.isoformat() if c.registered_at else None,
            "is_active": c.is_active,
        }
        for c in clients
    ]


@app.post(
    "/clients/register",
    response_model=RegisterClientResponse,
)
async def register_client(req: RegisterClientRequest):
    setup_token = get_setup_token()
    if req.setup_token != setup_token:
        raise HTTPException(status_code=401, detail="Invalid setup token")

    signed_cert_pem = _sign_csr(req.csr_pem)
    fingerprint = _cert_fingerprint(signed_cert_pem)

    ca_cert, _ = _load_or_create_ca()
    ca_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode()

    hospital_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        client = RegisteredClient(
            hospital_id=hospital_id,
            hospital_name=req.hospital_name,
            certificate_fingerprint=fingerprint,
        )
        db.add(client)
        await db.commit()

    return RegisterClientResponse(
        hospital_id=hospital_id,
        client_certificate_pem=signed_cert_pem,
        ca_certificate_pem=ca_pem,
    )


@app.get("/rounds", dependencies=[Depends(verify_api_key)])
async def list_rounds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RoundSchedule).order_by(desc(RoundSchedule.round_id))
    )
    rounds = result.scalars().all()
    return [
        {
            "round_id": r.round_id,
            "window_seconds": r.window_seconds,
            "expiry_timestamp": r.expiry_timestamp.isoformat()
            if r.expiry_timestamp
            else None,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rounds
    ]


@app.get("/rounds/{round_id}", dependencies=[Depends(verify_api_key)])
async def get_round(round_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RoundSchedule).where(RoundSchedule.round_id == round_id)
    )
    round_schedule = result.scalar_one_or_none()
    if round_schedule is None:
        raise HTTPException(status_code=404, detail="Round not found")

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.round_id == round_id)
    )
    model_version = result.scalar_one_or_none()

    return {
        "round": {
            "round_id": round_schedule.round_id,
            "window_seconds": round_schedule.window_seconds,
            "expiry_timestamp": round_schedule.expiry_timestamp.isoformat()
            if round_schedule.expiry_timestamp
            else None,
            "status": round_schedule.status,
            "created_at": round_schedule.created_at.isoformat()
            if round_schedule.created_at
            else None,
        },
        "model_version": {
            "val_dice": mv.val_dice,
            "val_iou": mv.val_iou,
            "epsilon": mv.epsilon,
            "is_active": mv.is_active,
        }
        if (mv := model_version)
        else None,
    }


_round_event = asyncio.Event()


@app.post("/rounds/start", dependencies=[Depends(verify_api_key)])
async def start_round(
    req: StartRoundRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(sa_func.max(RoundSchedule.round_id))
    )
    max_round = result.scalar()
    next_round = (max_round or 0) + 1

    now = datetime.now(timezone.utc)
    expiry = now.replace(second=0, microsecond=0)
    expiry = expiry.timestamp() + req.window_seconds
    expiry_dt = datetime.fromtimestamp(expiry, tz=timezone.utc)

    schedule = RoundSchedule(
        round_id=next_round,
        window_seconds=req.window_seconds,
        expiry_timestamp=expiry_dt,
        status="OPEN",
    )
    db.add(schedule)
    await db.commit()

    _round_event.set()
    _round_event.clear()

    return RoundSchema(
        round_id=next_round,
        window_seconds=req.window_seconds,
        expiry_timestamp=expiry_dt,
        status="OPEN",
    )


@app.post("/rollback", dependencies=[Depends(verify_api_key)])
async def rollback(round_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    checkpoint_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "checkpoints",
        f"round_{round_id}",
    )
    model_path = os.path.join(checkpoint_dir, "global_model.pth")
    if not os.path.exists(model_path):
        raise HTTPException(
            status_code=404,
            detail=f"Checkpoint for round {round_id} not found at {model_path}",
        )

    await db.execute(
        ModelVersion.__table__.update().values(is_active=False)
    )

    result = await db.execute(
        select(ModelVersion).where(ModelVersion.round_id == round_id)
    )
    mv = result.scalar_one_or_none()
    if mv:
        mv.is_active = True
    else:
        raise HTTPException(
            status_code=404,
            detail=f"ModelVersion for round {round_id} not found",
        )

    event = AuditEvent(
        event_type="model_rollback",
        round_id=round_id,
        details={"target_round": round_id, "triggered_by": "admin"},
    )
    db.add(event)
    await db.commit()

    return {"status": "rolled_back", "round": round_id}


@app.get("/audit-log", dependencies=[Depends(verify_api_key)])
async def get_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    round_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditEvent)
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if round_id is not None:
        query = query.where(AuditEvent.round_id == round_id)

    count_query = select(sa_func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(AuditEvent.timestamp))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    entries = result.scalars().all()

    return AuditLogPagination(
        total=total,
        page=page,
        limit=limit,
        entries=[
            AuditLogEntry(
                id=e.id,
                event_type=e.event_type,
                round_id=e.round_id,
                timestamp=e.timestamp,
                details=e.details,
            )
            for e in entries
        ],
    )


@app.get("/metrics/epsilon", dependencies=[Depends(verify_api_key)])
async def metrics_epsilon(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelVersion).order_by(ModelVersion.round_id)
    )
    versions = result.scalars().all()
    return [
        {
            "round_id": v.round_id,
            "epsilon": v.epsilon,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


@app.get("/metrics/dice", dependencies=[Depends(verify_api_key)])
async def metrics_dice(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelVersion).order_by(ModelVersion.round_id)
    )
    versions = result.scalars().all()
    return [
        {
            "round_id": v.round_id,
            "val_dice": v.val_dice,
            "val_iou": v.val_iou,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


# ---- WebSocket ----

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            async with AsyncSessionLocal() as db:
                active_result = await db.execute(
                    select(sa_func.count(RegisteredClient.hospital_id)).where(
                        RegisteredClient.is_active.is_(True)
                    )
                )
                active_clients = active_result.scalar() or 0

                round_result = await db.execute(
                    select(RoundSchedule).order_by(desc(RoundSchedule.round_id)).limit(1)
                )
                latest_round = round_result.scalar_one_or_none()

                dice_result = await db.execute(
                    select(ModelVersion).order_by(desc(ModelVersion.round_id)).limit(1)
                )
                latest_mv = dice_result.scalar_one_or_none()

            payload = {
                "active_clients": active_clients,
                "current_round": latest_round.round_id if latest_round else 0,
                "round_status": latest_round.status if latest_round else "NONE",
                "latest_dice": latest_mv.val_dice if latest_mv else 0.0,
                "latest_epsilon": latest_mv.epsilon if latest_mv else 0.0,
                "timestamp": int(time.time()),
            }

            await websocket.send_json(payload)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass



