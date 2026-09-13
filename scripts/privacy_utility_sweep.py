"""
scripts/privacy_utility_sweep.py
---------------------------------
Mukesh TASK 2/3 -- Privacy-utility sweep wrapper.

Loads existing E11 results from results/e11_training_results.json and
reformats them into a cross-tabulated privacy-utility table.
Also re-runs the sweep when --rerun flag is given.

Outputs:
    results/privacy_utility_sweep.csv
    results/privacy_utility_sweep.json
"""

import argparse
import csv
import json
import os
import sys


RESULTS_DIR = "results"
E11_JSON    = os.path.join(RESULTS_DIR, "e11_training_results.json")


def load_e11_results():
    if not os.path.exists(E11_JSON):
        print(f"[ERROR] {E11_JSON} not found. Run e11_empirical_sweep.py first.")
        sys.exit(1)
    with open(E11_JSON) as f:
        return json.load(f)


def build_table(data):
    rows = []
    for entry in data:
        # Accept both flat dicts and nested result structures
        sigma   = entry.get("sigma") or entry.get("noise_multiplier")
        clip    = entry.get("clip")  or entry.get("max_grad_norm", 1.0)
        rounds  = entry.get("rounds", 20)
        dice    = (entry.get("final_dice")
                   or entry.get("val_dice")
                   or entry.get("best_val_dice", float("nan")))
        epsilon = (entry.get("epsilon_final")
                   or entry.get("epsilon")
                   or (entry.get("accounting_regimes", {}).get("executed_empirical", {}).get("epsilon_20_round"))
                   or entry.get("final_epsilon", float("nan")))
        delta   = entry.get("delta", 1e-5)
        rows.append({
            "sigma": sigma, "clip": clip, "rounds": rounds,
            "delta": delta, "epsilon_final": epsilon,
            "dice_score": dice,
        })
    # Sort by sigma asc
    rows.sort(key=lambda r: (r["sigma"] or 0, r["clip"] or 0))
    return rows


def save_outputs(rows):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_path  = os.path.join(RESULTS_DIR, "privacy_utility_sweep.csv")
    json_path = os.path.join(RESULTS_DIR, "privacy_utility_sweep.json")

    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    with open(json_path, "w") as f:
        json.dump({"sweep": rows}, f, indent=2)

    return csv_path, json_path


def print_table(rows):
    print(f"\n{'sigma':>6} {'clip':>5} {'rounds':>6} {'epsilon':>10} {'dice':>8}")
    print("-" * 42)
    for r in rows:
        e = r["epsilon_final"]
        d = r["dice_score"]
        print(f"{r['sigma']:>6.1f} {r['clip']:>5.1f} {r['rounds']:>6d} "
              f"{(e if e is not None else float('nan')):>10.4f} "
              f"{(d if d is not None else float('nan')):>8.4f}")


def main():
    p = argparse.ArgumentParser(description="Privacy-Utility Sweep")
    p.add_argument("--rerun", action="store_true",
                   help="Re-run E11 sweep (calls e11_empirical_sweep.py)")
    args = p.parse_args()

    if args.rerun:
        import subprocess
        print("[INFO] Re-running E11 sweep ...")
        subprocess.run([sys.executable, "e11_empirical_sweep.py"], check=True)

    data = load_e11_results()
    # Handle list or dict-with-list
    if isinstance(data, dict):
        data = data.get("rows") or data.get("results") or data.get("sweep") or list(data.values())
    if not data:
        print("[ERROR] No entries found in e11_training_results.json")
        sys.exit(1)

    rows = build_table(data)
    print_table(rows)
    csv_path, json_path = save_outputs(rows)
    print(f"\nSaved: {csv_path}\nSaved: {json_path}")


if __name__ == "__main__":
    main()
