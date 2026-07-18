from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from platform.coordinator.strategy import FullSDFLProductionStrategy
from platform.coordinator.config import get_coordinator_secret

def build_server_app(
    num_rounds: int = 10,
    window_seconds: int = 300,
    mu: float = 0.001,
    C: float = 2.0,
    sigma: float = 1.5,
) -> ServerApp:

    strategy = FullSDFLProductionStrategy(
        mu=mu,
        C=C,
        sigma=sigma,
        secret_key=get_coordinator_secret(),
        window_seconds=window_seconds,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
    )

    def server_fn(context):
        return ServerAppComponents(
            strategy=strategy,
            config=ServerConfig(num_rounds=num_rounds)
        )

    return ServerApp(server_fn=server_fn)

server_app = build_server_app()
