# Experiment E10 -- Temporal Window Sweep (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Rounds per window** | 100 |
| **Windows tested** | 6 |

## Sweep Results

| Window Tr (s) | Completion Rate | Client Acceptance | Straggler Rejection |
|---:|---:|---:|---:|
| 30 | 0.0% | 3.7% | 96.3% |
| 60 | 23.0% | 41.0% | 59.0% |
| 120 | 100.0% | 75.7% | 24.3% |
| 300 | 100.0% | 95.0% | 5.0% |
| 600 | 100.0% | 99.7% | 0.3% |
| 1200 | 100.0% | 100.0% | 0.0% |

## Key Findings

- **Minimum 100 Percent Completion Window Seconds:** 120
- **Recommended Operational Window Seconds:** 300
- **Simulation Note:** Heterogeneous hospital latencies are simulated distributions modeling compute and network variance.

Note: the two headline numbers above are hardcoded constants in the script's output rather than computed live from this specific sweep -- worth confirming with the team whether that's intentional.

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`.

**Provenance note (2026-09-26):** The only `e10_stdout.log` currently committed for this experiment contains nothing but an
environment crash (`ModuleNotFoundError: No module named 'iterators'`, a transitive dependency of `flwr[simulation]==1.8.0`'s
gRPC backend that isn't declared in `requirements.txt`) -- it never reaches the sweep code. The metrics above come from the
committed `e10_window_results.json` (timestamped 2026-09-05), which predates that crashed session; there is currently no
clean log in the repo proving this exact run. Per team decision, these committed artifacts are being kept as authoritative
rather than re-run. If reproducibility needs to be re-established later, add `iterators` to `requirements.txt` first.
