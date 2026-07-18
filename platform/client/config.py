import os
from dotenv import load_dotenv

load_dotenv()

def get_client_id() -> str:
    val = os.getenv("CLIENT_ID")
    if not val:
        raise ValueError("CLIENT_ID environment variable missing")
    return val

def get_client_secret() -> str:
    val = os.getenv("CLIENT_SECRET")
    if not val:
        raise ValueError("CLIENT_SECRET environment variable missing")
    return val

def get_coordinator_url() -> str:
    return os.getenv("COORDINATOR_URL", "https://coordinator.sdfl-vendor.com")

def get_flower_address() -> str:
    return os.getenv("FLOWER_SERVER_ADDRESS", "coordinator.sdfl-vendor.com:8080")

def get_epsilon_threshold() -> float:
    return float(os.getenv("EPSILON_KILL_THRESHOLD", "3.0"))

def get_local_db_path() -> str:
    return os.getenv("LOCAL_DB_PATH", "/data/client.db")

def get_incoming_dir() -> str:
    return os.getenv("LOCAL_INCOMING_DIR", "/data/incoming")
