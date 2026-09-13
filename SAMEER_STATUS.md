# SAMEER STATUS REPORT

## Completed Work
- **Phase 1: Repository Audit:** Examined dataset config, `e7_temporal.py` aggregator logic, AES-GCM encryption flow, and FL simulation hooks.
- **Phase 2: Experiment Infrastructure:** Created `experiment_config.py`, `result_utils.py`, and `experiment_runner.py` to systematize testing without rewriting Sanjay's/Mukesh's core files. Handled automated json/csv logging with git hashes and runtime metadata.
- **Phase 3: Temporal Window Experiment (E10):** Implemented `temporal_window_experiment.py` which profiles an empirical $p_{95}$ latency by running a legitimate client epoch, then tests varying windows relative to $p_{95}$. Tests legitimate completion and late rejections.
- **Phase 4: Scalability Evaluation (E14):** Implemented `scalability_experiment.py`. It correctly demarcates real-hospital evaluations (N=3) from simulated client scaling (N=5, 10, 20). Measures server key generation, certificate generation, validation, memory overhead, and communication payload sizes.
- **Phase 5: Fault & Late-Client Robustness (E15):** Implemented `fault_injection.py`. Validates AES-GCM integrity failure modes, certificate modifications, missing participants, key context mismatches, client dropouts, and expired updates.
- **Phase 10: Documentation:** Wrote `SAMEER_EXPERIMENTS.md` outlining exact execution methodology and constraints.

## Files Created
- `scripts/experiment_config.py`
- `scripts/result_utils.py`
- `scripts/experiment_runner.py`
- `scripts/temporal_window_experiment.py`
- `scripts/scalability_experiment.py`
- `scripts/fault_injection.py`
- `scripts/plot_results.py`
- `SAMEER_EXPERIMENTS.md`
- `SAMEER_STATUS.md`

## Files Modified
None! I preserved the integrity of the team's core files by implementing the experiments strictly via wrappers, custom client instantiations, and localized testing loops.

## Commands Executed
- Setup Virtual Environment & dependencies (Using Homebrew Python 3.11).
- `python3 scripts/make_splits.py`
- `python3 scripts/temporal_window_experiment.py`
- `python3 scripts/scalability_experiment.py --exp_name E14`
- `python3 scripts/fault_injection.py --exp_name E15`
- `python3 scripts/plot_results.py`

## Experiments Completed
- E10 Temporal Window ($p_{95}$ profiled as 365.5s, tested windows from 60s to 731s).
- E14 Scalability (Simulated N=3, 5, 10, 20 taking ~4.1 hours to fully compute client epochs).
- E15 Fault Injection (10 unique faults successfully validated with precise rejection mapping).
- All final plots (`E10_temporal_window.png`, `E14_scalability.png`) and markdown tables (`E15_robustness_table.md`) generated.

## Failures & Unresolved Issues
- System Python Anaconda 3.11 was broken. Workaround: Used Homebrew `/opt/homebrew/bin/python3.11`.
- `cryptography.exceptions.InvalidTag` during E14 testing due to assigning mismatched key contexts. Workaround: Moved `generate_round_key` outside the client loop in `scalability_experiment.py` so all clients correctly share a round's ephemeral key.
- Matplotlib font cache and Pandas dependencies blocked initial plotting script. Workaround: Rewrote plotting scripts to use standard `csv` library.

## Dependencies on Sanjay
- Relies on `TemporalCheckpointingSecAgg` interface stability. E15 validation strictly expects validation to raise graceful errors (e.g. returning `False, "invalid_signature"`) rather than completely crashing the FL round.
- Expects `crypto.client_encrypt` to consistently return a dictionary with `nonce` and `ciphertext` concatenated with its MAC tag.

## Dependencies on Mukesh
- Relies on Opacus wrapper maintaining consistent parameter structures for the UNet++ models.
- If DP parameter `max_grad_norm` shifts, it will slightly perturb the $p_{95}$ legitimate time profiled in E10.

## Exact Next Steps
- Review generated plots in `results/`.
- Merge infrastructure scripts into master branch.
- Finalize the temporal window parameter configuration based on the newly generated empirical $p_{95}$ data.
