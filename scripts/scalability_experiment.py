import os
import sys
import time
import json
import tracemalloc
import torch
import numpy as np
import copy
from typing import Dict, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.experiment_config import ExperimentConfig
from scripts.result_utils import ResultTracker
from scripts.experiment_runner import ExperimentRunner

from e7_temporal import TemporalHospitalClient, TemporalCheckpointingSecAgg
import flwr as fl
import crypto

class ScalabilityExperiment(ExperimentRunner):
    def setup(self):
        if self.config.smoke_test:
            self.client_counts = [3, 5]
            self.local_epochs = 1
        else:
            self.client_counts = [3, 5, 10, 20]
            self.local_epochs = 1
            
        from model import ResUNetPlusPlus
        from e4_dpsgd import fix_model_for_opacus
        self.model = ResUNetPlusPlus()
        fix_model_for_opacus(self.model)
        self.dummy_params = [val.cpu().numpy() for _, val in self.model.state_dict().items()]
        
    def run_simulated_round(self, N):
        """Simulate a round of FL with N clients to measure time and memory"""
        print(f"--- Simulating round for N={N} clients ---")
        is_real_hospital = (N == 3)
        print(f"Evaluation type: {'REAL HOSPITALS' if is_real_hospital else 'SIMULATED CLIENT SCALING'}")
        
        # We will measure everything here directly by invoking the functions
        
        # 1. SERVER: Certificate Generation
        tracemalloc.start()
        start = time.perf_counter()
        
        strategy = TemporalCheckpointingSecAgg(
            mu=0.001, C=2.0, sigma=1.5, secret_key=b"test_key", window_seconds=300
        )
        import uuid
        key_context_id = str(uuid.uuid4())
        participants = [f"client_{i}" for i in range(N)]
        
        cert = crypto.create_certificate(
            round_id=1,
            model_hash="dummy",
            participants=participants,
            key_context_id=key_context_id,
            expiry_timestamp=time.time() + 300
        )
        signature = crypto.sign_certificate(cert, b"test_key")
        
        cert_time = time.perf_counter() - start
        current, peak = tracemalloc.get_traced_memory()
        server_mem_cert = peak
        tracemalloc.stop()
        
        # 2. CLIENT: Local training & encryption
        client_train_times = []
        client_enc_times = []
        client_memories = []
        
        ciphertexts = []
        ct_sizes = []
        fit_results = []
        
        round_key = crypto.generate_round_key()
        strategy.round_keys[key_context_id] = round_key
        
        for i in range(N):
            tracemalloc.start()
            start = time.perf_counter()
            
            # Simulated dataset: for real hospitals we'd use hid={0,1,2}, for simulated we assign hid=0 but it's just for tracing
            client = TemporalHospitalClient(hospital_id=i % 3, local_epochs=self.local_epochs, mu=0.001, max_grad_norm=2.0, noise_multiplier=1.5)
            
            # Train
            config = {
                "round_key_hex": round_key.hex(),
                "certificate": json.dumps(cert),
                "signature": signature,
                "key_context_id": key_context_id
            }
            if self.config.smoke_test:
                time.sleep(0.1) # fake training for smoke test
            else:
                try:
                    res = client.fit(self.dummy_params, config)
                except Exception as e:
                    print(f"Client fit error: {e}")
                    
            train_time = time.perf_counter() - start
            client_train_times.append(train_time)
            
            # Encrypt
            start_enc = time.perf_counter()
            
            # Extract weights to encrypt
            dummy_weights = torch.cat([torch.tensor(p).flatten() for p in self.dummy_params])
            ct = crypto.client_encrypt(dummy_weights, round_key)
            
            enc_time = time.perf_counter() - start_enc
            client_enc_times.append(enc_time)
            
            current, peak = tracemalloc.get_traced_memory()
            client_memories.append(peak)
            tracemalloc.stop()
            
            ciphertexts.append(ct)
            ct_sizes.append(len(ct["nonce"]) + len(ct["ciphertext"]))
            fit_res_metrics = {
                "nonce_hex": ct["nonce"].hex(),
                "ciphertext_hex": ct["ciphertext"].hex(),
                "certificate": json.dumps(cert),
                "signature": signature,
                "key_context_id": key_context_id
            }
            
            class DummyClientProxy:
                def __init__(self, cid):
                    self.cid = cid
                    
            class DummyFitRes:
                def __init__(self, metrics):
                    self.metrics = metrics
                    self.parameters = fl.common.ndarrays_to_parameters(self.dummy_params)
            DummyFitRes.dummy_params = self.dummy_params
            
            fit_results.append((DummyClientProxy(f"client_{i}"), DummyFitRes(fit_res_metrics)))
            
        # 3. SERVER: Validation
        start = time.perf_counter()
        valid_updates = []
        for c, res in fit_results:
            is_valid, reason = strategy.validate_update(res)
            if is_valid:
                valid_updates.append(res)
        val_time = time.perf_counter() - start
        
        # 4. SERVER: Decryption
        start = time.perf_counter()
        decrypted_weights = []
        for i, ct in enumerate(ciphertexts):
            dec = crypto.decrypt_update(ct, strategy.round_keys[key_context_id])
            decrypted_weights.append(dec)
        dec_time = time.perf_counter() - start
        
        # 5. SERVER: Key Destruction
        start = time.perf_counter()
        crypto.destroy_round_key(strategy.round_keys[key_context_id])
        key_dest_time = time.perf_counter() - start
        
        # Output sizes
        avg_ct_size = np.mean(ct_sizes)
        total_rx = sum(ct_sizes)
        
        result = {
            "num_clients": N,
            "is_real_hospital": is_real_hospital,
            "evaluation_type": "real" if is_real_hospital else "simulated_scaling",
            "server_cert_time": cert_time,
            "client_train_time_mean": np.mean(client_train_times),
            "client_enc_time_mean": np.mean(client_enc_times),
            "client_memory_mean": np.mean(client_memories),
            "server_val_time": val_time,
            "server_dec_time": dec_time,
            "server_key_dest_time": key_dest_time,
            "avg_ciphertext_size_bytes": avg_ct_size,
            "total_rx_bytes": total_rx
        }
        self.tracker.add_result(result)
        
    def _execute_experiment(self):
        for count in self.client_counts:
            self.run_simulated_round(count)

if __name__ == "__main__":
    runner = ScalabilityExperiment()
    runner.run()
