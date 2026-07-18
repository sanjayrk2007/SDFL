import os, base64
from dotenv import load_dotenv

load_dotenv()

def get_coordinator_secret() -> bytes:
    encoded = os.getenv("COORDINATOR_SECRET")
    if not encoded:
        raise ValueError("COORDINATOR_SECRET environment variable missing")
    try:
        decoded = base64.b64decode(encoded)
    except Exception as e:
        raise ValueError("COORDINATOR_SECRET is not a valid base64-encoded string") from e
    if len(decoded) != 32:
        raise ValueError("COORDINATOR_SECRET must decode to exactly 32 bytes")
    return decoded

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable missing")
    return url

def get_api_key() -> str:
    key = os.getenv("API_DASHBOARD_KEY")
    if not key:
        raise ValueError("API_DASHBOARD_KEY environment variable missing")
    return key
