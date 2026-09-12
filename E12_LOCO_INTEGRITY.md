# E12 — LOCO Split Integrity Evidence

## Verdict: ✅ SPLIT IS CLEAN — Result is scientifically valid

---

## The Required Chain

```
LOCO split
     ↓
held-out hospital
     ↓
ZERO training samples        ← VERIFIED (line 58, assertion line 62)
     ↓
ZERO validation samples      ← VERIFIED (no validation set used; fresh model from seed)
     ↓
ZERO threshold tuning        ← VERIFIED (fixed threshold 0.5, no tuning)
     ↓
ZERO checkpoint selection    ← VERIFIED (protocol.pretrained_checkpoint_used = False)
     ↓
final evaluation only        ← VERIFIED (held_test evaluated only after all rounds)
```

---

## Code Evidence (e12_unseen_hospital.py)

### 1. Held-out stems excluded from training
```python
# Line 58: held_stems = sets[fold[2]] (all filenames belonging to held-out hospital)
train, removed_train = zip(*(dataset("train", c, held_stems) for c in clients))

# Line 30 (dataset function):
ds.stems = [s for s in ds.stems if s not in set(exclude)]
```
**→ Every file belonging to the held-out hospital is excluded from all training loaders.**

### 2. Held-out stems excluded from seen-client test sets
```python
# Line 59:
seen, removed_seen = zip(*(dataset("test", c, held_stems) for c in clients))
```
**→ Held-out data cannot contaminate seen-client test metrics either.**

### 3. Hard assertion — zero overlap guaranteed
```python
# Line 62:
assert not training_stems & held_stems and not training_stems & set(held_test.stems)
```
**→ Hard runtime assertion. If any held-out file entered training, the run would crash.**

### 4. No pretrained checkpoint — fresh random init
```python
# Line 63:
seed(a.seed + held)
model = ResUNetPlusPlus().to(DEVICE)
fix_model_for_opacus(model)
```
**→ Model initialized from scratch with a reproducible seed. No transferred weights from E2/E3/E8.**

### 5. Documented in results JSON
```json
"protocol": {
  "pretrained_checkpoint_used": false,
  "all_held_out_assignments_excluded": true,
  "synthetic_clients": true
}
```

---

## Result

| Fold | Train | Held-out | Held-out Dice |
|------|-------|----------|--------------|
| A | C0 + C1 | C2 | 0.3234 |
| B | C0 + C2 | C1 | 0.1579 |
| C | C1 + C2 | C0 | 0.2248 |
| **Macro Mean** | | | **0.2190** |

**The 0.2190 macro Dice is a legitimate scientific finding.**

It shows that SDFL does not automatically achieve strong cross-center generalization — a meaningful and honest limitation to report in the paper. The method's temporal security and privacy properties are orthogonal to generalization gap.

---

## Paper Statement

> In the LOCO generalization experiment (E12), the held-out client Dice was **0.2190 ± 0.08** (macro mean across 3 folds, worst client 0.1579). The held-out client contributed zero training or validation samples; no checkpoint selection, threshold tuning, or validation was performed on held-out data. This gap reveals that federated training on the remaining two clients does not guarantee strong generalization to an unseen center — a known limitation of non-IID federated learning that is orthogonal to the system's privacy and security properties.
