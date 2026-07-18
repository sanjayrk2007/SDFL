import os
import json
import time
import datetime
import asyncio
import torch
import flwr as fl

from e7_temporal import TemporalCheckpointingSecAgg
from e8_server import FullSDFLStrategy
from model import ResUNetPlusPlus
from e4_dpsgd import fix_model_for_opacus, set_parameters
from platform.coordinator.config import get_coordinator_secret
from platform.coordinator.db import AsyncSessionLocal, AuditEvent

# Async helper to write database events
async def async_write_audit_event(event_type: str, round_id: int, details: dict):
    try:
        async with AsyncSessionLocal() as session:
            new_event = AuditEvent(
                event_type=event_type,
                round_id=round_id,
                details=details
            )
            session.add(new_event)
            await session.commit()
    except Exception as e:
        print(f"Error writing audit event to PostgreSQL: {e}")

def write_postgresql_audit(event_type: str, round_id: int = None, details: dict = None):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        loop.create_task(async_write_audit_event(event_type, round_id, details))
    else:
        loop.run_until_complete(async_write_audit_event(event_type, round_id, details))

class FullSDFLProductionStrategy(FullSDFLStrategy):
    def __init__(
        self,
        mu,
        C,
        sigma,
        secret_key=None,
        window_seconds=300,
        coordinator_url=None,
        checkpoint_dir="checkpoints/",
        *args,
        **kwargs
    ):
        if secret_key is None:
            secret_key = get_coordinator_secret()
        
        super().__init__(
            mu=mu,
            C=C,
            sigma=sigma,
            secret_key=secret_key,
            window_seconds=window_seconds,
            *args,
            **kwargs
        )
        self.coordinator_url = coordinator_url
        self.checkpoint_dir = checkpoint_dir

    def configure_fit(self, server_round, parameters, client_manager):
        fit_configs = super().configure_fit(server_round, parameters, client_manager)
        write_postgresql_audit(
            event_type="round_open",
            round_id=server_round,
            details={"Tr": self.current_Tr}
        )
        return fit_configs

    def aggregate_fit(self, server_round, results, failures):
        params, metrics = super().aggregate_fit(server_round, results, failures)
        
        # Check if aggregate fit succeeded or expired
        if params is not None:
            write_postgresql_audit(
                event_type="round_close",
                round_id=server_round,
                details={"status": "success"}
            )
        else:
            write_postgresql_audit(
                event_type="round_expired_no_aggregation",
                round_id=server_round,
                details={"reason": "no_valid_updates_or_decryption_failed"}
            )
        
        # Key is destroyed in the finally block of super().aggregate_fit
        write_postgresql_audit(
            event_type="key_destroyed",
            round_id=server_round,
            details={}
        )
        
        return params, metrics

    def aggregate_evaluate(self, server_round, results, failures):
        agg_loss, avg_metrics = super().aggregate_evaluate(server_round, results, failures)
        
        # After each round save global model to checkpoints/round_{N}/
        if self.latest_ndarrays is not None:
            round_dir = os.path.join(self.checkpoint_dir, f"round_{server_round}")
            os.makedirs(round_dir, exist_ok=True)
            
            # Save PyTorch Model weights
            model_path = os.path.join(round_dir, "global_model.pth")
            model_to_save = ResUNetPlusPlus().to("cpu")
            fix_model_for_opacus(model_to_save)
            set_parameters(model_to_save, self.latest_ndarrays)
            torch.save(model_to_save.state_dict(), model_path)
            
            # Save metrics JSON
            metrics_path = os.path.join(round_dir, "metrics.json")
            val_dice = self.latest_metrics.get("val_dice", 0.0)
            val_iou = self.latest_metrics.get("val_iou", 0.0)
            epsilon = self.latest_metrics.get("epsilon", 0.0)
            
            metrics_data = {
                "val_dice": val_dice,
                "val_iou": val_iou,
                "epsilon": epsilon,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            with open(metrics_path, "w") as f:
                json.dump(metrics_data, f, indent=2)
                
        return agg_loss, avg_metrics
