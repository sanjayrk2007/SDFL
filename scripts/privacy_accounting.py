"""
scripts/privacy_accounting.py
-------------------------------
Mukesh TASK 2 -- Standalone privacy accounting utility.

Computes cumulative (eps, delta)-DP guarantees using Opacus RDP accountant.
Usage:
    python scripts/privacy_accounting.py [--sigma SIGMA] [--clip C]
                                         [--q Q] [--steps STEPS]
                                         [--rounds ROUNDS] [--delta DELTA]
                                         [--sweep]

With --sweep, prints a full grid table to stdout and saves:
    results/privacy_accounting_sweep.csv
    results/privacy_accounting_sweep.json
"""

import argparse
import csv
import json
import os

try:
    from opacus.accountants import RDPAccountant
    _OPACUS = True
except ImportError:
    _OPACUS = False


def _opacus_epsilon(sigma, q, steps, delta):
    acc = RDPAccountant()
    acc.history = [(sigma, q, steps)]
    eps, _ = acc.get_privacy_spent(delta=delta)
    return float(eps)


def _manual_epsilon(sigma, q, steps, delta):
    import math
    alphas = [2, 5, 10, 25, 50, 100]
    best_eps = float("inf")
    for alpha in alphas:
        rdp_per_step = alpha * q ** 2 / (2 * sigma ** 2)
        rdp_total = rdp_per_step * steps
        eps_delta = rdp_total + math.log(1.0 / delta) / (alpha - 1)
        if eps_delta < best_eps:
            best_eps = eps_delta
    return best_eps


def compute_epsilon(sigma, clip, q, steps, rounds, delta):
    total_steps = steps * rounds
    if _OPACUS:
        eps = _opacus_epsilon(sigma, q, total_steps, delta)
        method = "opacus_rdp"
    else:
        eps = _manual_epsilon(sigma, q, total_steps, delta)
        method = "manual_rdp"
    return {
        "sigma": sigma, "clip": clip, "q": q,
        "steps_per_round": steps, "rounds": rounds,
        "total_steps": total_steps, "delta": delta,
        "epsilon_final": round(eps, 6), "method": method,
    }


SWEEP_SIGMAS = [0.3, 0.5, 0.8, 1.0, 1.5, 2.0]
SWEEP_CLIPS  = [0.5, 1.0]
SWEEP_ROUNDS = [20]
SWEEP_Q      = 8 / 612
SWEEP_STEPS  = 76
SWEEP_DELTA  = 1e-5


def run_sweep(out_dir="results"):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for sigma in SWEEP_SIGMAS:
        for clip in SWEEP_CLIPS:
            for rounds in SWEEP_ROUNDS:
                rows.append(compute_epsilon(sigma, clip, SWEEP_Q, SWEEP_STEPS, rounds, SWEEP_DELTA))

    print(f"{'sigma':>6} {'clip':>5} {'rounds':>6} {'q':>10} {'delta':>8} {'epsilon':>12}  method")
    print("-" * 60)
    for r in rows:
        print(f"{r['sigma']:>6.1f} {r['clip']:>5.1f} {r['rounds']:>6d} "
              f"{r['q']:>10.6f} {r['delta']:>8.0e} {r['epsilon_final']:>12.6f}  {r['method']}")

    csv_path = os.path.join(out_dir, "privacy_accounting_sweep.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    json_path = os.path.join(out_dir, "privacy_accounting_sweep.json")
    with open(json_path, "w") as f:
        json.dump({"sweep": rows}, f, indent=2)

    print(f"\nSaved: {csv_path}\nSaved: {json_path}")
    return rows


def main():
    p = argparse.ArgumentParser(description="SDFL Privacy Accounting")
    p.add_argument("--sigma",  type=float, default=1.5)
    p.add_argument("--clip",   type=float, default=1.0)
    p.add_argument("--q",      type=float, default=8/612)
    p.add_argument("--steps",  type=int,   default=76)
    p.add_argument("--rounds", type=int,   default=20)
    p.add_argument("--delta",  type=float, default=1e-5)
    p.add_argument("--sweep",  action="store_true")
    args = p.parse_args()

    if args.sweep:
        run_sweep()
    else:
        print(json.dumps(compute_epsilon(args.sigma, args.clip, args.q, args.steps, args.rounds, args.delta), indent=2))


if __name__ == "__main__":
    main()
