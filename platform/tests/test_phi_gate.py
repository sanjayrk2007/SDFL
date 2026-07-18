import asyncio
import os
import tempfile

import numpy as np
from PIL import Image


def test_phi_gate_passes_clean_image():
    img = Image.fromarray(
        np.random.randint(0, 200, (256, 256, 3), dtype=np.uint8)
    )
    from scripts.sanitize import sanitize

    out, passed = sanitize(img)
    assert isinstance(out, Image.Image)
    assert isinstance(passed, bool)


def test_epsilon_kill_fires_at_threshold():
    from platform.client.db import init_db, log_epsilon
    from platform.client.epsilon_guard import check_epsilon_kill

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    asyncio.run(init_db(db_path))
    asyncio.run(log_epsilon(db_path, 1, 3.1))
    os.environ["LOCAL_DB_PATH"] = db_path
    os.environ["EPSILON_KILL_THRESHOLD"] = "3.0"

    try:
        killed, eps = check_epsilon_kill()
        assert killed is True
        assert eps >= 3.0
    finally:
        os.unlink(db_path)
