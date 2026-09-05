import os
import json
import csv
import time
import subprocess
import platform
import sys

def get_git_info():
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.STDOUT).decode().strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.STDOUT).decode().strip()
        return commit_hash, branch
    except Exception:
        return "unknown", "unknown"

def get_hardware_info():
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version()
    }
    try:
        import torch
        info["pytorch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
    except ImportError:
        info["pytorch_version"] = "not_installed"
    return info

class ResultTracker:
    def __init__(self, config):
        self.config = config.to_dict() if hasattr(config, "to_dict") else config
        self.results = []
        self.start_time = time.time()
        self.commit_hash, self.branch = get_git_info()
        self.hardware_info = get_hardware_info()
        self.status = "running"
        self.errors = []
        
        os.makedirs(self.config.get("output_path", "results"), exist_ok=True)

    def add_result(self, result_dict):
        self.results.append(result_dict)

    def set_error(self, error_msg):
        self.status = "error"
        self.errors.append(error_msg)

    def save(self):
        end_time = time.time()
        runtime = end_time - self.start_time
        if self.status == "running":
            self.status = "completed"

        data = {
            "experiment_name": self.config.get("exp_name"),
            "timestamp": time.time(),
            "git_commit_hash": self.commit_hash,
            "branch": self.branch,
            "seed": self.config.get("seed"),
            "configuration": self.config,
            "hardware_info": self.hardware_info,
            "runtime": runtime,
            "status": self.status,
            "errors": self.errors,
            "results": self.results
        }

        # Save JSON
        json_path = os.path.join(self.config.get("output_path", "results"), f"{self.config.get('exp_name')}_results.json")
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)

        # Save CSV
        if self.results:
            csv_path = os.path.join(self.config.get("output_path", "results"), f"{self.config.get('exp_name')}_results.csv")
            keys = self.results[0].keys()
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.results)
                
        return json_path
