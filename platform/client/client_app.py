import asyncio
from flwr.client import ClientApp
from e8_server import FullSDFLClient
from e2_server import hospital_loaders
from platform.client.config import (
    get_epsilon_threshold, get_local_db_path
)
from platform.client.db import get_max_epsilon

def client_fn(context):
    hid = int(context.node_config.get("partition-id", 0))

    # Epsilon kill check before participating
    db_path = get_local_db_path()
    threshold = get_epsilon_threshold()
    
    # Run the async query synchronously using asyncio.run
    current_eps = asyncio.run(get_max_epsilon(db_path))
    if current_eps >= threshold:
        raise RuntimeError(
            f"Epsilon kill threshold reached "
            f"({current_eps:.4f} >= {threshold}). "
            f"Client refusing to participate."
        )

    # In Flower 1.x partition-id maps to client loaders
    train_loader, val_loader = hospital_loaders[hid]
    client = FullSDFLClient(
        hospital_id=hid,
        local_epochs=1,
        mu=0.001,
        max_grad_norm=2.0,
        noise_multiplier=1.5,
    )
    return client.to_client()

client_app = ClientApp(client_fn=client_fn)
