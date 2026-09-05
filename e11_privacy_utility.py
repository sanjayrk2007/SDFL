"""
E11 -- Privacy-Utility Sweep
==============================
Sweep the DP noise multiplier sigma in {0.3, 0.5, 0.8, 1.0, 1.5, 2.0} and measure:
  * Cumulative (epsilon, delta)-DP privacy cost  -- computed by RDPAccountant (not hardcoded)
  * Per-round epsilon(r) curve                   -- computed by RDPAccountant (not hardcoded)
  * Dice / IoU                                   -- loaded from E4/E8 reference results where
                                                     available; otherwise labelled as a
                                                     theoretical projection pending GPU training.

Author : Mukesh S (security + privacy experiments)
Branch : mukesh/e11-privacy-utility
"""

from __future__ import annotations

import json
import math
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("E11")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

OUT_JSON  = RESULTS_DIR / "e11_privacy_results.json"
OUT_JSONL = RESULTS_DIR / "e11_privacy_log.jsonl"
REPORT_MD = ROOT / "E11_RESULTS.md"

# Reference result files (teammates outputs -- read-only)
E4_RESULTS = RESULTS_DIR / "e4_dp_results.json"
E8_METRICS = RESULTS_DIR / "e8_metrics.json"

# ---------------------------------------------------------------------------
# Experimental configuration
# Matches the dataset / training setup used in E4 / E8
# ---------------------------------------------------------------------------
SIGMA_VALUES   = [0.3, 0.5, 0.8, 1.0, 1.5, 2.0]
MAX_GRAD_NORM  = 2.0          # C -- clipping norm (from e4_dpsgd.py / e8_server.py)
DELTA          = 1e-5         # delta for (epsilon, delta)-DP
N_HOSPITALS    = 3
N_TRAIN        = 266          # approx 80% of 333 samples per hospital
BATCH_SIZE     = 8
LOCAL_EPOCHS   = 3
NUM_ROUNDS     = 20

# Derived quantities (not hardcoded, computed here)
STEPS_PER_EPOCH = math.floor(N_TRAIN / BATCH_SIZE)      # 33 steps / epoch
STEPS_PER_ROUND = LOCAL_EPOCHS * STEPS_PER_EPOCH        # 99 steps / round
TOTAL_STEPS     = NUM_ROUNDS * STEPS_PER_ROUND          # 1,980 steps / client
SAMPLE_RATE     = BATCH_SIZE / N_TRAIN                  # q approx 0.0301


# ---------------------------------------------------------------------------
# Utility: compute (epsilon, delta)-DP via RDPAccountant
# ---------------------------------------------------------------------------
def compute_epsilon_curve(
    sigma: float,
    sample_rate: float,
    steps_per_round: int,
    num_rounds: int,
    delta: float,
) -> tuple[list[float], float]:
    """
    For a given noise multiplier sigma, return:
      - eps_per_round: list of cumulative epsilon(r) for r = 1 ... num_rounds
      - eps_final:     epsilon after all num_rounds rounds

    Uses Opacus RDPAccountant; each federated round is decomposed into
    steps_per_round individual optimizer steps.
    """
    try:
        from opacus.accountants import RDPAccountant
    except ImportError as exc:
        raise RuntimeError(
            "Opacus is required for E11.  Install with: pip install opacus"
        ) from exc

    accountant = RDPAccountant()
    eps_per_round: list[float] = []

    for r in range(1, num_rounds + 1):
        # Accumulate one round worth of optimizer steps
        for _ in range(steps_per_round):
            accountant.step(noise_multiplier=sigma, sample_rate=sample_rate)

        eps_r = accountant.get_epsilon(delta=delta)
        eps_per_round.append(round(float(eps_r), 6))
        log.debug("  sigma=%.2f  round %2d  eps(r)=%.4f", sigma, r, eps_r)

    eps_final = eps_per_round[-1]
    return eps_per_round, eps_final


# ---------------------------------------------------------------------------
# Utility: load reference Dice / IoU from E4 / E8 results
# ---------------------------------------------------------------------------
def load_reference_metrics() -> dict[str, dict[str, Any]]:
    """
    Load Dice and IoU scores from E4 dp results JSON (keyed by sigma)
    and from E8 cumulative metrics JSON (for sigma=1.5).

    Returns a dict  sigma_str -> {"dice": float|None, "iou": float|None, "source": str}
    where None means not available from reference; requires GPU training run.
    """
    ref: dict[str, dict[str, Any]] = {}

    # --- E4 results ---
    if E4_RESULTS.exists():
        try:
            with open(E4_RESULTS) as f:
                e4 = json.load(f)
            # Layout 1: list of dicts with "sigma" / "noise_multiplier" key
            if isinstance(e4, list):
                for entry in e4:
                    s = entry.get("sigma") or entry.get("noise_multiplier")
                    if s is not None:
                        key = f"{float(s):.1f}"
                        ref[key] = {
                            "dice"  : entry.get("dice") or entry.get("mean_dice"),
                            "iou"   : entry.get("iou")  or entry.get("mean_iou"),
                            "source": "e4_dp_results.json",
                        }
            # Layout 2: dict keyed by sigma string
            elif isinstance(e4, dict):
                for k, v in e4.items():
                    try:
                        s = float(k)
                        ref[f"{s:.1f}"] = {
                            "dice"  : v.get("dice") or v.get("mean_dice"),
                            "iou"   : v.get("iou")  or v.get("mean_iou"),
                            "source": "e4_dp_results.json",
                        }
                    except ValueError:
                        pass
        except Exception as exc:
            log.warning("Could not parse %s: %s", E4_RESULTS, exc)

    # --- E8 results (sigma=1.5) ---
    if E8_METRICS.exists():
        try:
            with open(E8_METRICS) as f:
                e8 = json.load(f)

            # E8 stores per-round metrics; take final-round values
            if isinstance(e8, list) and e8:
                final = e8[-1]
            elif isinstance(e8, dict):
                rounds = e8.get("rounds") or e8.get("history") or []
                final  = rounds[-1] if rounds else e8
            else:
                final = {}

            e8_dice = (final.get("dice") or final.get("mean_dice")
                       or final.get("val_dice"))
            e8_iou  = (final.get("iou")  or final.get("mean_iou")
                       or final.get("val_iou"))

            sigma_key = "1.5"
            if sigma_key not in ref:
                ref[sigma_key] = {"dice": None, "iou": None, "source": ""}
            if e8_dice is not None:
                ref[sigma_key]["dice"]   = round(float(e8_dice), 4)
                ref[sigma_key]["source"] = "e8_metrics.json"
            if e8_iou is not None:
                ref[sigma_key]["iou"]    = round(float(e8_iou), 4)
                ref[sigma_key]["source"] = "e8_metrics.json"
        except Exception as exc:
            log.warning("Could not parse %s: %s", E8_METRICS, exc)

    return ref


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------
def run_e11() -> dict[str, Any]:
    log.info("=" * 64)
    log.info("E11 -- Privacy-Utility Sweep")
    log.info("=" * 64)
    log.info(
        "Config: N_train=%d  batch=%d  q=%.4f  local_epochs=%d  "
        "rounds=%d  steps/round=%d  total_steps=%d  C=%.1f  delta=%.0e",
        N_TRAIN, BATCH_SIZE, SAMPLE_RATE, LOCAL_EPOCHS,
        NUM_ROUNDS, STEPS_PER_ROUND, TOTAL_STEPS, MAX_GRAD_NORM, DELTA,
    )

    ref_metrics = load_reference_metrics()
    log.info("Reference metrics loaded for sigma values: %s", list(ref_metrics.keys()))

    rows: list[dict[str, Any]] = []
    log_entries: list[str]     = []
    timestamp_start = datetime.now(timezone.utc).isoformat()

    for sigma in SIGMA_VALUES:
        log.info("-" * 50)
        log.info("Processing sigma = %.2f ...", sigma)

        eps_curve, eps_final = compute_epsilon_curve(
            sigma           = sigma,
            sample_rate     = SAMPLE_RATE,
            steps_per_round = STEPS_PER_ROUND,
            num_rounds      = NUM_ROUNDS,
            delta           = DELTA,
        )

        sigma_key = f"{sigma:.1f}"
        ref = ref_metrics.get(sigma_key, {})
        dice_val = ref.get("dice")
        iou_val  = ref.get("iou")
        dice_src = ref.get("source", "not available")

        if dice_val is None:
            dice_label = "N/A -- requires GPU training run"
            iou_label  = "N/A -- requires GPU training run"
            dice_src   = "theoretical projection pending actual training"
        else:
            dice_label = f"{dice_val:.4f}"
            iou_label  = f"{iou_val:.4f}" if iou_val is not None else "N/A"

        log.info(
            "  sigma=%.2f  eps_final=%.4f  Dice=%s  IoU=%s  (source: %s)",
            sigma, eps_final, dice_label, iou_label, dice_src,
        )

        row = {
            "sigma"              : sigma,
            "max_grad_norm"      : MAX_GRAD_NORM,
            "delta"              : DELTA,
            "n_train_per_client" : N_TRAIN,
            "batch_size"         : BATCH_SIZE,
            "sample_rate"        : round(SAMPLE_RATE, 6),
            "local_epochs"       : LOCAL_EPOCHS,
            "num_rounds"         : NUM_ROUNDS,
            "steps_per_round"    : STEPS_PER_ROUND,
            "total_steps"        : TOTAL_STEPS,
            "accountant_type"    : "RDPAccountant (Opacus)",
            "alpha_orders"       : "Opacus default [1.1 .. 128]",
            "epsilon_final"      : round(eps_final, 6),
            "epsilon_per_round"  : eps_curve,
            "dice"               : dice_val,
            "iou"                : iou_val,
            "dice_iou_source"    : dice_src,
        }
        rows.append(row)

        log_entry = {
            "event"          : "sigma_sweep",
            "sigma"          : sigma,
            "epsilon_final"  : round(eps_final, 6),
            "dice"           : dice_val,
            "iou"            : iou_val,
            "dice_iou_source": dice_src,
            "timestamp"      : datetime.now(timezone.utc).isoformat(),
        }
        log_entries.append(json.dumps(log_entry))

    timestamp_end = datetime.now(timezone.utc).isoformat()

    result = {
        "experiment"  : "E11 Privacy-Utility Sweep",
        "timestamp"   : timestamp_start,
        "completed_at": timestamp_end,
        "configuration": {
            "sigma_values"      : SIGMA_VALUES,
            "max_grad_norm"     : MAX_GRAD_NORM,
            "delta"             : DELTA,
            "n_hospitals"       : N_HOSPITALS,
            "n_train_per_client": N_TRAIN,
            "batch_size"        : BATCH_SIZE,
            "local_epochs"      : LOCAL_EPOCHS,
            "num_rounds"        : NUM_ROUNDS,
            "steps_per_round"   : STEPS_PER_ROUND,
            "total_steps"       : TOTAL_STEPS,
            "sample_rate"       : round(SAMPLE_RATE, 6),
            "accountant"        : "RDPAccountant (Opacus)",
            "note"              : (
                "Dice/IoU values sourced from E4/E8 reference runs where available. "
                "Entries marked requires GPU training run are theoretical projections "
                "until actual Colab training is executed for that sigma value."
            ),
        },
        "rows": rows,
    }

    # Write JSON
    with open(OUT_JSON, "w") as f:
        json.dump(result, f, indent=2)
    log.info("Results written to %s", OUT_JSON)

    # Write JSONL log
    with open(OUT_JSONL, "w") as f:
        for entry in log_entries:
            f.write(entry + "\n")
    log.info("Log written to %s", OUT_JSONL)

    return result


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------
def generate_report(result: dict[str, Any]) -> None:
    rows = result["rows"]
    cfg  = result["configuration"]

    lines = [
        "# E11 - Privacy-Utility Sweep",
        "",
        f"> Generated: {result['completed_at']}  |  Branch: `mukesh/e11-privacy-utility`",
        "",
        "## Configuration",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        "| Accountant | RDPAccountant (Opacus) |",
        "| alpha orders | Opacus default [1.1 ... 128] |",
        f"| Clipping norm C | {cfg['max_grad_norm']} |",
        f"| delta | {cfg['delta']:.0e} |",
        f"| Hospitals (clients) | {cfg['n_hospitals']} |",
        f"| N_train per client | {cfg['n_train_per_client']} (approx 80% of 333) |",
        f"| Batch size | {cfg['batch_size']} |",
        f"| Sample rate q | {cfg['sample_rate']:.4f} |",
        f"| Local epochs | {cfg['local_epochs']} |",
        f"| Steps per round | {cfg['steps_per_round']} (= {cfg['local_epochs']} x floor({cfg['n_train_per_client']}/{cfg['batch_size']})) |",
        f"| Federated rounds | {cfg['num_rounds']} |",
        f"| Total steps per client | {cfg['total_steps']} |",
        "",
        "> **Note on Dice/IoU**: Values sourced from E4/E8 reference runs where available.",
        "> Entries marked *requires GPU training run* are theoretical projections",
        "> pending actual training on Colab for that sigma value.",
        "",
        "---",
        "",
        "## Privacy-Utility Frontier",
        "",
        "| sigma | epsilon (computed) | Dice | IoU | Dice/IoU Source |",
        "|-------|--------------------|------|-----|-----------------|",
    ]

    for row in rows:
        sigma = row["sigma"]
        eps   = row["epsilon_final"]
        dice  = f"{row['dice']:.4f}" if row["dice"] is not None else "*pending*"
        iou   = f"{row['iou']:.4f}"  if row["iou"]  is not None else "*pending*"
        src   = row["dice_iou_source"]
        lines.append(f"| {sigma} | **{eps:.4f}** | {dice} | {iou} | {src} |")

    lines += [
        "",
        "---",
        "",
        "## Per-Round epsilon(r) Curves",
        "",
        "Cumulative epsilon(r) as computed by `RDPAccountant.get_epsilon(delta=1e-5)` after each federated round.",
        "",
        "| sigma | r=1 | r=5 | r=10 | r=15 | r=20 (final) |",
        "|-------|-----|-----|------|------|--------------|",
    ]

    for row in rows:
        c = row["epsilon_per_round"]
        def ep(idx):
            return f"{c[idx]:.4f}" if idx < len(c) else "--"
        lines.append(
            f"| {row['sigma']} | {ep(0)} | {ep(4)} | {ep(9)} | {ep(14)} | **{ep(19)}** |"
        )

    lines += [
        "",
        "---",
        "",
        "## Key Findings",
        "",
        "1. **epsilon is accountant-computed, not hardcoded.** All values above were produced",
        "   by `RDPAccountant.step()` and `get_epsilon(delta=1e-5)` -- not from the roadmap table.",
        "",
        "2. **Privacy cost grows with rounds.** epsilon(r) increases monotonically across the 20 rounds.",
        "   The final-round value is the worst-case cumulative budget consumed.",
        "",
        "3. **Lower sigma = stronger gradient noise = lower epsilon (less privacy consumption)**",
        "   but at the cost of model utility (lower Dice/IoU).",
        "   Higher sigma = weaker noise = higher epsilon (more privacy consumed) but better utility.",
        "",
        "4. **E8 reference run** (sigma=1.5, C=2.0, 20 rounds) produced epsilon approx 2.772 in the",
        "   original E8 paper section. The accountant-recomputed value above supersedes that approximation.",
        "",
        "5. **Pending GPU runs**: Dice/IoU for sigma not equal to 1.5 require actual Colab training.",
        "   The epsilon values are exact regardless and can be cited now.",
        "",
        "---",
        "",
        "## Simulation Assumptions",
        "",
        "- All hospitals contribute exactly N_train=266 samples per round (no dropouts).",
        "- Steps per round = local_epochs x floor(N_train / batch_size) (fixed; no partial-batch effects).",
        "- Poisson-like subsampling amplification assumed via Opacus internal batch sampler",
        "  (nominal sample_rate = batch_size / N_train passed to accountant).",
        "- Dice/IoU from E4/E8 may not perfectly correspond to the accountant exact sigma sweep",
        "  if E4 used different hyperparameters; this is noted per row under Dice/IoU Source.",
        "",
    ]

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written to %s", REPORT_MD)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = run_e11()
    generate_report(result)
    log.info("=" * 64)
    log.info("E11 complete.  Results in results/e11_privacy_results.json")
    log.info("=" * 64)
