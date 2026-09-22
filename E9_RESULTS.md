# E9 — Retrospective Breach Attack Experiment

## Summary

| Metric | Result |
|---|---:|
| Trials per condition | 1000 |
| Total attack attempts | 5000 |
| Successful plaintext recoveries | 0 |
| Empirical attack success rate | 0.00% |
| 95% confidence interval | 0.00%–0.30% |
| Rule-of-Three 95% upper bound | 0.30% |

## Attack Conditions

| Condition | Trials | Successes | Success Rate |
|---|---:|---:|---:|
| A1_zeroed_key_exploit | 1000 | 0 | 0.0000% |
| A2_random_key_search | 1000 | 0 | 0.0000% |
| A3_cross_round_substitution | 1000 | 0 | 0.0000% |
| A4_certificate_tampering | 1000 | 0 | 0.0000% |
| A5_plaintext_reconstruction | 1000 | 0 | 0.0000% |

## Interpretation

Across the 5,000 attack attempts, no successful plaintext recoveries were observed under the tested retrospective breach conditions.

The observed empirical attack success rate was 0.00%.

## Generated Artifacts

- `results/e9_breach_results.json`
- `results/e9_conditions.csv`
- `results/e9_stdout.log`
- `figures/e9_attack_success.png`
- `figures/e9_attack_success.pdf`
