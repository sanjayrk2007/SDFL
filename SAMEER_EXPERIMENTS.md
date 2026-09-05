# SDFL - Sameer's Experiments

## Overview
This document describes the experiment infrastructure and methodology designed by Sameer for Phase 3 (E10), Phase 4 (E14), and Phase 5 (E15) of the SDFL research project. The goal of this infrastructure is to run robust, reproducible benchmarks on the SDFL temporal and scalability capabilities without unnecessarily altering the core ML and security components built by Mukesh and Sanjay.

## Experiment Infrastructure

The infrastructure revolves around a base runner class and automated data recording:
- `scripts/experiment_config.py`: Exposes a standard set of flags and configurations across all tests.
- `scripts/result_utils.py`: Captures runtime metadata (git commit, branch, hardware specs, python/pytorch versions, timestamps) and serializes experiment results into JSON and CSV files automatically.
- `scripts/experiment_runner.py`: A base class providing a `setup()` and `_execute_experiment()` structure that handles fault-tolerance and ensures results are saved even if an experiment aborts midway.

### Configuration Parameters
All experiments accept standard arguments:
- `--exp_name`: Name for the JSON/CSV outputs
- `--smoke_test`: Skips heavy operations for rapid CI/testing
- `--num_rounds`, `--local_epochs`, `--num_clients`, `--temporal_window`

### Result Locations
Outputs are placed in the `results/` directory as `{exp_name}_results.json` and `{exp_name}_results.csv`.

## Methodologies

### Phase 3: Temporal Window Experiment (E10)
**File**: `scripts/temporal_window_experiment.py`
**Methodology**: 
1. We execute one actual local epoch through `TemporalHospitalClient` to profile the realistic legitimate completion latency ($p_{50}$ and $p_{95}$).
2. We test multiple temporal window points around this empirical $p_{95}$ latency, simulating updates arriving comfortably before, exactly at, and after expiry.
3. We measure legitimate completion rates, late rejection rates, and security lifetime overhead without relying on artificial bounds.

### Phase 4: Scalability Evaluation (E14)
**File**: `scripts/scalability_experiment.py`
**Methodology**:
- **Real-Hospital (N=3):** Evaluates exact overhead and communication using the true stratified non-IID hospital split configuration.
- **Simulated Client Scaling (N=5, 10, 20):** Because the actual Kvasir dataset partitions are constrained, N > 3 tests use *explicitly labeled* simulated scaling. Clients are mapped round-robin to the baseline splits purely to measure memory scaling, cryptographic overhead, and bytes transmitted, rather than claiming existence of new medical centers.
- Metrics are traced using `time.perf_counter()` and `tracemalloc`.

### Phase 5: Fault & Late-Client Robustness (E15)
**File**: `scripts/fault_injection.py`
**Methodology**:
We wrap `TemporalCheckpointingSecAgg` in a dummy FL loop and systematically inject:
- Expired updates (delayed beyond Tr)
- Ciphertext truncations
- Ciphertext single-byte modifications (tests AES-GCM tag integrity during decryption rather than superficial validation)
- Certificate participant spoofing
- Invalid key context submissions
- Replay attacks
- Cross-round substitution (attempting to use Round 1 certs in Round 2)

**Evaluation Criteria**: We ensure the server fails securely via graceful rejections and exception handling rather than system crashing.

## Reproducibility
To reproduce the suite:
1. `python3 scripts/make_splits.py` (Generate true N=3 dataset partitions)
2. `python3 scripts/temporal_window_experiment.py`
3. `python3 scripts/scalability_experiment.py`
4. `python3 scripts/fault_injection.py`

## Team Dependencies
- **Sanjay (Security):** Relies on `crypto.py` and `TemporalCheckpointingSecAgg`. The key context generation and validation are treated as a black box. Any internal AES-GCM or HMAC updates must maintain the existing signature structures.
- **Mukesh (Privacy):** Relies on `e4_dpsgd.py` and Opacus instrumentation. If DP limits are altered, profiling latencies in E10 may shift.
