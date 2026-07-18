import asyncio

from platform.client.db import get_max_epsilon, log_epsilon
from platform.client.config import get_epsilon_threshold, get_local_db_path


def check_epsilon_kill() -> tuple[bool, float]:
    db_path = get_local_db_path()
    threshold = get_epsilon_threshold()
    current = asyncio.run(get_max_epsilon(db_path)) or 0.0
    return current >= threshold, current


def record_round_epsilon(round_id: int, epsilon: float):
    db_path = get_local_db_path()
    asyncio.run(log_epsilon(db_path, round_id, epsilon))
