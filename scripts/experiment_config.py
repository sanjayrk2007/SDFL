import os
import json
import argparse

class ExperimentConfig:
    def __init__(self, **kwargs):
        self.exp_name = kwargs.get("exp_name", "experiment")
        self.seed = kwargs.get("seed", 42)
        self.num_rounds = kwargs.get("num_rounds", 5)
        self.local_epochs = kwargs.get("local_epochs", 1)
        self.num_clients = kwargs.get("num_clients", 3)
        self.hospital_split = kwargs.get("hospital_split", "hospital_splits.json")
        self.dp_params = kwargs.get("dp_params", {"mu": 0.001, "C": 2.0, "sigma": 1.5})
        self.temporal_window = kwargs.get("temporal_window", 10.0)
        self.checkpoint_path = kwargs.get("checkpoint_path", "checkpoints")
        self.output_path = kwargs.get("output_path", "results")
        self.dry_run = kwargs.get("dry_run", False)
        self.smoke_test = kwargs.get("smoke_test", False)

    def to_dict(self):
        return {
            "exp_name": self.exp_name,
            "seed": self.seed,
            "num_rounds": self.num_rounds,
            "local_epochs": self.local_epochs,
            "num_clients": self.num_clients,
            "hospital_split": self.hospital_split,
            "dp_params": self.dp_params,
            "temporal_window": self.temporal_window,
            "checkpoint_path": self.checkpoint_path,
            "output_path": self.output_path,
            "dry_run": self.dry_run,
            "smoke_test": self.smoke_test
        }

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("--exp_name", type=str, default="experiment")
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--num_rounds", type=int, default=5)
        parser.add_argument("--local_epochs", type=int, default=1)
        parser.add_argument("--num_clients", type=int, default=3)
        parser.add_argument("--temporal_window", type=float, default=10.0)
        parser.add_argument("--dry_run", action="store_true")
        parser.add_argument("--smoke_test", action="store_true")
        args, _ = parser.parse_known_args()
        return ExperimentConfig(**vars(args))
