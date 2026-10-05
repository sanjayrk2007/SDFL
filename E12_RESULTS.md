# E12 — Synthetic Client-Holdout Generalization Ablation

> Entry-point: `e12_unseen_hospital.py`
> Branch: `mukesh/sdfl-completion`

---

## Protocol Disclosure

> **Important Scope Clarification:** E12 is a **plain FedAvg generalization ablation**, not a full SDFL-stack experiment. It does **not** use differential privacy (DP-SGD), temporal certificates, or AES-GCM encryption. Its purpose is to measure cross-client generalization of the model under standard federated aggregation with synthetic client splits.
>
> Furthermore, the "hospital" splits are **synthetic overlapping size-biased subsets** of the Kvasir-SEG dataset, not independently collected real hospital cohorts. The held-out client received zero training, validation, or model-selection data.

---

## LOCO Split Integrity (Verified)

All five chain links were verified from source code:

| Check | Implementation | Verified |
|-------|---------------|---------|
| Held-out stems excluded from training | `ds.stems = [s for s in ds.stems if s not in exclude]` (line 30) | ✅ |
| Held-out stems excluded from seen-client test sets | Same exclusion on `split="test"` loaders (line 59) | ✅ |
| Hard runtime assertion: zero overlap | `assert not training_stems & held_stems` (line 62) | ✅ |
| No pretrained checkpoint loaded | Fresh `ResUNetPlusPlus()` from seed (line 63) | ✅ |
| Recorded in results JSON | `"pretrained_checkpoint_used": false` | ✅ |

---

## Configuration

| Parameter | Value |
|-----------|-------|
| Folds | 3 (A: hold out C2, B: hold out C1, C: hold out C0) |
| Rounds | 20 |
| Local epochs | 1 |
| Batch size | 8 |
| Learning rate | 1e-4 |
| Optimizer | Adam (no DP-SGD) |
| Model initialization | Seeded random (no checkpoint) |

---

## Results

| Fold | Train Clients | Held-out | Seen-Client Dice | Held-out Dice | IoU | Precision | Recall |
|------|--------------|----------|-----------------|--------------|-----|-----------|--------|
| **A** | C0 + C1 | C2 | — | **0.3234** | — | — | — |
| **B** | C0 + C2 | C1 | — | **0.1579** | — | — | — |
| **C** | C1 + C2 | C0 | — | **0.2248** | — | — | — |
| **Macro Mean** | | | | **0.2190** | | | |
| **Worst Client** | | | | **0.1579** | | | |

---

## Scientific Interpretation

The macro Dice of **0.2190** is a legitimate and honest finding. It shows that standard federated training on 2 synthetic clients does not guarantee strong generalization to the third unseen partition. This reflects the known non-IID generalization gap in federated learning.

**This result should be reported in the paper as-is** — it is not a failure or error. The paper narrative should clearly state:
1. Client assignments are synthetic and overlapping (not real separate hospital data collections).
2. The generalization experiment uses plain FedAvg (no DP or security layers).
3. This result is orthogonal to the temporal security and privacy contributions of SDFL.

---

## Paper Statement

> *"In a leave-one-client-out generalization experiment (E12), SDFL trained on two of three synthetic hospital partitions achieves a macro mean Dice of 0.2190 (worst client: 0.1579) on the held-out partition. Client partitions are synthetic, overlapping subsets of Kvasir-SEG and do not represent independently collected hospital cohorts; this result characterizes within-dataset non-IID generalization limits rather than true cross-center generalization."*
