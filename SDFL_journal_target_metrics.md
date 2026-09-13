# SDFL journal target metrics

##### [**Undermind**](https://undermind.ai)

---

# SDFL journal target metrics

## Executive conclusion

The current SDFL results are not yet ready to support a strong journal claim. The main problem is not that the model is below colorectal-segmentation state of the art; it is that the full SDFL model currently retains only about **53.8% of the FedAvg Dice** and has an absolute Dice loss of **0.3567**. For a standard in-domain test, Full SDFL Dice of **0.4145** is weak. A Dice value in the 0.40–0.50 range can be defensible only if the experiment is explicitly framed as a severe privacy or out-of-domain stress test, the less-private ablations show the expected trade-off, and the temporal-security evidence is unusually strong.

The practical submission target should be:

- **Utility:** Full SDFL Dice at least **0.60**, preferably **0.65–0.72**, with at least **85% utility retention relative to FedAvg**. A stronger paper would reach **0.72 or higher** and keep the SDFL–FedAvg gap below **0.05–0.08 Dice**.
- **Privacy:** Recompute privacy from the complete training run. Report cumulative **record- or patient-level** $`(\epsilon,\delta)`$, with $`\delta\le 10^{-5}`$ or a justified bound tied to the number of protected units. A final $`\epsilon`$ of **2–5** is a credible target for record-level DP; **$`\epsilon\approx 2–3`$** is reasonable if it is exact and cumulative. It is not automatically strong for client-level DP with only a few hospitals.
- **Temporal security:** For every primary attack class, target **0 successful attacks in at least 1,000 independent attempts per condition**, with exact 95% confidence bounds. The paper also needs a formal argument about key erasure, backups, crash recovery, clock handling, and retained global models.
- **Generalization:** Use a genuinely unseen center. Target at least **0.60 Dice** as a minimum, **0.68–0.75** for a solid journal, and **0.75 or higher** for a strong result, while keeping seen-to-unseen degradation below **20%** where possible.
- **Systems:** Keep full SDFL within about **10% of the matched FedAvg runtime** for a solid journal and within **5%** for a strong result. AES-GCM and certificate handling should add little payload beyond the model update. The current absolute encryption and aggregation times look promising, but they cannot be judged without relative denominators.

These are not universal acceptance thresholds. The literature does not define a single Dice, epsilon, or overhead cutoff for privacy/security papers. The ranges below combine measured values from comparable studies, reviewer-expectation inferences, and explicit engineering targets.

## How to read the targets

- **\[L\] Literature-supported:** directly observed in a relevant paper or benchmark.
- **\[R\] Reviewer-expectation inference:** a reasoned expectation from comparable studies, not a formal field-wide standard.
- **\[E\] Engineering target:** recommended for this paper because it makes the SDFL claim credible; it is not a universal threshold.

A target is only meaningful when the dataset split, privacy unit, number of rounds, attack capabilities, hardware, and metric definition are reported alongside it.

## What the literature actually supports

Polyp segmentation on the same dataset often reports Dice around **0.81–0.92**, but cross-dataset and difficult sequence performance is much lower. ResUNet++ reported about **0.85 Dice on Kvasir-SEG**, about **0.64 on ETIS-Larib**, and about **0.46–0.50 on Kvasir-Sessile**; cross-dataset video tests reached roughly **0.28–0.40** Dice \[1\]. On PolypGen, unseen single-frame performance was roughly **0.76–0.82 Dice**, while unseen sequence performance was roughly **0.62–0.71** \[2\]. A federated domain-generalization study reported approximately **0.86–0.87 Dice** on unseen Kvasir-SEG, but that result used a dedicated domain-generalization method and did not include SDFL’s privacy stack \[3\].

Federated polyp studies report much higher values when each center’s test data remains close to the training distribution. Fan et al. reported FedAvg Dice from **0.828 to 0.901** across four datasets, but did not perform a true unseen-center test \[4\]. PolypDB reported a strong three-center FedAvg benchmark, with an overall Dice of about **0.955** for the best architecture, but again this is not a direct benchmark for a heavily privatized SDFL model \[5\]. These results should not be used as a universal lower bound for a security paper, but they do show that a full in-domain Dice of 0.41 requires a serious explanation.

In medical segmentation more broadly, federated models often remain close to centralized models when privacy noise is absent or modest. FednnU-Net reported federated results close to centralized results across multiple modalities, including external center testing \[6\]. In FeTS benchmarking, FedAvg obtained **0.891 mean Dice** versus **0.903 centralized** on a large multi-institution brain-tumor setup, while the limited-data setup was lower at about **0.806 versus 0.815** \[7\]. In cross-silo segmentation, FedAvg was within about one to two Dice points of centralized learning on several tasks, although individual held-out sites could be much harder \[8\].

Privacy can impose a real utility cost. Ziller et al. reported federated DP Dice values around **0.83–0.91** depending on architecture and privacy regime, with some architectures failing to converge \[9\]. Adnan et al. reported cumulative **$`\epsilon=2.90`$, $`\delta=10^{-4}`$** and external accuracy of **0.707**, compared with **0.741** for standard FL and **0.768** for centralized training \[10\]. Kaissis et al. reported **$`\epsilon=6.0`$, $`\delta=1.9\times10^{-4}`$** and a moderate classification utility loss while preventing usable inversion in their setting \[11\]. By contrast, client-level DP with only a few medical sites can be much more expensive: Jia et al. reported cumulative epsilon values above **100** for their six-client prostate segmentation experiments, with high-noise Dice around **0.58–0.59** for the best configurations \[12\].

The conclusion is that a low SDFL Dice can be scientifically defensible under a very restrictive privacy setting, but it should not be presented as normal clinical segmentation quality. The paper must show the full privacy–utility frontier rather than reporting only the weakest final model.

## Utility target table

| Metric | Minimum publishable | Good journal target | Strong target | Evidence and interpretation |
|:---|---:|---:|---:|:---|
| Centralized Dice | 0.75–0.80 \[R\] | 0.80–0.86 \[E\] | $`\ge 0.86`$ \[E\] | Same-dataset polyp studies commonly reach 0.81–0.92, but the exact split and architecture matter \[1\], \[5\]. |
| FedAvg Dice | $`\ge 0.70`$ \[E\] | 0.75–0.80 \[E\] | $`\ge 0.80`$ \[E\] | Current 0.7712 is already a credible non-private FL baseline if the split is sound. Cross-silo studies often keep FedAvg close to centralized performance \[7\], \[8\]. |
| Full SDFL Dice | 0.55–0.60 \[E\] | 0.65–0.72 \[E\] | 0.72–0.78 \[E\] | For ordinary in-domain testing, 0.4145 is weak. The 0.40–0.50 range is defensible mainly for difficult OOD, sessile, or very strong-DP stress tests \[1\], \[2\], \[9\], \[12\]. |
| IoU | 0.40–0.50 \[E\] | 0.50–0.60 \[E\] | $`\ge 0.60`$ \[E\] | Polyp cross-dataset IoU can be roughly 0.64–0.76, while difficult cases are lower \[1\], \[13\]. Current 0.2994 is a red flag for an in-domain main result. |
| Precision and recall | Both $`\ge 0.65`$, recall preferably $`\ge 0.70`$ \[E\] | Both $`\ge 0.75`$ \[E\] | Both $`\ge 0.80`$ \[E\] | No universal cutoff exists. Report both because high precision with poor recall can hide missed polyps. PolypGen unseen-sequence recall was about 0.70–0.73 for strong models \[2\]. |
| HD95 or surface distance | No universal absolute cutoff \[L\] | No more than 10% worse than FedAvg \[E\] | Equal to or better than FedAvg \[E\] | HD95 depends on pixel spacing, image size, and annotation quality. Report median, IQR, and center-wise values; do not compare raw pixel HD95 across incompatible datasets \[3\], \[6\], \[14\]. |

### Is Full SDFL Dice of 0.40–0.50 acceptable?

**For a normal in-domain test: generally no.** It places the model near the difficult-sessile or cross-domain failure regime rather than the usual federated segmentation regime. Current Full SDFL Dice of 0.4145 is therefore not a satisfactory final utility result by itself.

**For a security-focused paper: conditionally.** It could be accepted as a deliberately stressed operating point if all of the following are true:

- the privacy setting is formally strong and cumulatively accounted;
- the same model and training schedule show substantially higher Dice in the FedAvg, AES-only, certificate, and expiry-without-destruction controls;
- the security gain is demonstrated by attacks rather than by a checklist alone;
- the paper labels the result as a privacy–utility trade-off, not as clinically ready segmentation;
- the model still has useful recall and does not collapse into mostly empty or overfilled masks;
- a less restrictive operating point reaches at least the good-journal range.

A paper that reports only Full SDFL Dice of 0.41 and 0% post-expiry attack success would still be vulnerable to the reviewer response that the system achieves security by making the learned model unusable.

### Utility retention is the main comparison

Use FedAvg as the primary utility reference because SDFL is a federated protocol contribution, not a new segmentation architecture. Define:

``` math
\text{Utility retention} = \frac{\text{Dice}_{\text{SDFL}}}{\text{Dice}_{\text{FedAvg}}}\times 100.
```

The current value is:

``` math
\frac{0.4145}{0.7712}\times 100 \approx 53.8\%.
```

Recommended interpretation:

- **Below 70%:** weak and difficult to defend \[E\].
- **70–85%:** minimum-to-acceptable depending on privacy strength and threat model \[R/E\].
- **85–92%:** good journal target \[E\].
- **Above 92%:** strong target, especially if the temporal mechanism adds negligible utility loss beyond AES-GCM and certificates \[E\].

The absolute Dice should still be reported. Relative retention cannot rescue a very low absolute score.

## Privacy accounting targets

There is no accepted universal epsilon threshold for medical AI. The useful comparison is whether epsilon is **exact, cumulative, tied to a clear adjacency definition, and paired with attack results**. Comparable medical studies have reported cumulative record-level values around **2.9**, **3.5**, and **6.0**, while other federated settings have produced values above **10** or even above **100** when the privacy unit is a whole client or hospital \[9\], \[10\], \[11\], \[12\], \[15\].

### Privacy target table

| Item | Minimum publishable | Good journal target | Strong target | Evidence and interpretation |
|:---|---:|---:|---:|:---|
| Final cumulative epsilon | Exact value $`\le 8`$ \[E\] | $`\epsilon\le 5`$ \[R/E\] | $`\epsilon\le 2–3`$ \[R/E\] | Values around 2.9–6.0 are directly reported in medical privacy studies, but no field-wide cutoff exists \[9\], \[10\], \[11\]. |
| Delta | $`\delta\le 10^{-4}`$ with justification \[E\] | $`\delta\le 10^{-5}`$ \[E\] | $`\delta\le 10^{-6}`$ where feasible \[E\] | Common studies use $`10^{-4}`$ or $`10^{-5}`$; a defensible rule is $`\delta\le 1/N`$ for the protected units, with a more conservative fixed value if practical \[9\], \[10\], \[15\]. |
| Privacy unit | Explicit record-level or patient-level adjacency \[L/R\] | Patient-level adjacency for medical claims \[E\] | Patient-level plus separate client-level analysis \[E\] | Slice-level accounting is not automatically patient-level for a multi-slice scan. Jia et al. show that client-level DP with few sites can be very costly \[12\]. |
| Accounting | RDP or PRV accountant over all rounds \[E\] | RDP/PRV with conversion details and privacy curve \[E\] | Independent recomputation or cross-check with a second accountant \[E\] | One-round or server-side approximations are not enough for a multi-round claim \[9\], \[10\], \[12\]. |
| Reporting | Noise multiplier, clipping, sampling, local steps, rounds, and final epsilon/delta \[E\] | Per-round and cumulative privacy curves \[E\] | Full sensitivity and hyperparameter-selection accounting \[E\] | Validation, model selection, and repeated tuning can consume privacy budget and must not be silently ignored \[15\]. |

### Is epsilon approximately 2–3 reasonable?

**Yes, conditionally.** It is a credible and relatively strong target for **record-level** DP when it is the final cumulative value over the entire training run, with a stated delta and accountant. Adnan et al. reported $`\epsilon=2.90,\delta=10^{-4}`$ in a medical FL experiment \[10\].

It is not enough to say “epsilon = 2.772” if the value is a server-side approximation, a one-round estimate, or not tied to patient-level adjacency. If the mechanism is client-level DP over only three or six hospitals, epsilon 2–3 may be much harder to obtain and should not be treated as an ordinary target.

### Required DP reporting

The final paper should report:

- adjacency unit: sample, patient, image, scan, or hospital;
- whether DP is local, central, distributed, or client-level;
- clipping norm and whether clipping is per-example, per-client, or per-update;
- noise multiplier and exact Gaussian mechanism;
- client sampling rate and record sampling rate;
- number of local steps, epochs, and communication rounds;
- whether the same individual can appear in multiple rounds;
- the RDP/PRV orders and conversion to $`(\epsilon,\delta)`$-DP;
- epsilon as a function of round number and the final cumulative value;
- the delta choice and why it is appropriate;
- privacy cost of validation, model selection, and hyperparameter search;
- whether secure aggregation is needed for the stated threat model;
- the exact software/accountant version and numerical precision;
- utility and attack metrics at several epsilon values, not just one operating point.

Do not claim that AES-GCM, key destruction, or ciphertext deletion changes the DP epsilon. Those mechanisms address different threat surfaces.

## Temporal-security evaluation

The main contribution should be tested as a protocol property, not as a five-row pass/fail demo. Secure-aggregation literature stresses that confidentiality, integrity, model consistency, dropout behavior, and malicious-server behavior are separate properties \[16\]. Pasquini et al. showed that a malicious server can exploit model inconsistency even when secure aggregation itself is cryptographically intact \[17\]. MedLeak showed that medical data can be recovered from aggregated updates under a crafted-server attack \[18\].

### Security target table

| Attack or event | Minimum publishable target | Good journal target | Strong target | Required evidence |
|:---|---:|---:|---:|:---|
| Timely valid update | $`\ge 99\%`$ accepted \[E\] | $`\ge 99.9\%`$ \[E\] | 100% in tested conditions \[E\] | Include boundary cases just before and at the deadline, network jitter, and clock skew. |
| Expired update | 0 accepted in 1,000 attempts \[E\] | 0 in 5,000 attempts \[E\] | 0 in 10,000 attempts plus deterministic rule/proof \[E\] | Test multiple expiry offsets, including milliseconds and seconds after $`T_r`$. |
| Replay | 0 accepted in 1,000 attempts \[E\] | 0 in 5,000 attempts \[E\] | 0 in 10,000 attempts across same-round and cross-round replays \[E\] | Test duplicate packets, reordered packets, retransmissions, and replay after restart. |
| Certificate tampering | 0 accepted in 1,000 attempts \[E\] | 0 in 5,000 attempts \[E\] | 0 in 10,000 attempts with every certificate field modified \[E\] | Bind the certificate to AES-GCM AAD and report which check rejects the packet. |
| Wrong key context | 0 accepted in 1,000 attempts \[E\] | 0 in 5,000 attempts \[E\] | 0 in 10,000 attempts across all round-key substitutions \[E\] | Include old key, future key, wrong-client key, and destroyed-key cases. |
| Cross-round substitution | 0 accepted in 1,000 attempts \[E\] | 0 in 5,000 attempts \[E\] | 0 in 10,000 attempts plus formal binding argument \[E\] | Bind round ID, model hash, certificate digest, and key-context ID. |
| Post-destruction decryption | 0 authenticated plaintexts in 1,000 attempts \[E\] | 0 in 5,000 attempts \[E\] | 0 in 10,000 attempts plus key-erasure evidence \[E\] | A failed AES-GCM tag is not enough if a backup key, process memory, or snapshot still exists. |

For a binomial attack-success rate with zero successes in $`n`$ independent trials, the approximate one-sided 95% upper bound is $`3/n`$. Thus, 0/100 implies an upper bound of roughly 3%, while 0/1,000 implies roughly 0.3%. This is why 0% from five or ten tests is not persuasive.

### Recommended security test matrix

Run each test over:

- at least five federated rounds;
- at least three independent protocol seeds or fresh key schedules;
- all clients and at least one dropout/retransmission condition;
- multiple timestamp boundary offsets;
- clean shutdown and crash/restart paths;
- packet duplication, delay, reordering, truncation, and bit flips;
- wrong model hash, wrong round ID, wrong certificate, wrong participant, and wrong key context;
- server-side retained ciphertext, server snapshot, and authorized audit-log artifacts.

The security paper should report both **acceptance/rejection** and **reason for rejection**. A failure count without trace-level diagnosis makes it hard to show that the intended temporal mechanism, rather than an unrelated parser error, caused the result.

## Retrospective breach experiment

The retrospective threat model should be stated narrowly:

> After expiry, an attacker obtains the retained ciphertext, nonce, authentication tag, certificate, signature, metadata, audit records, and any explicitly in-scope server snapshots, but not the destroyed round key or an authorized live decryption service.

The attacker should not be allowed to use an artifact that the system claims to delete unless the threat model explicitly includes forensic recovery from storage or backups. Conversely, the paper must not claim protection against an attacker who copied the plaintext update, key, or decrypted model during the valid window. Temporal expiry limits later protocol recoverability; it does not undo earlier disclosure.

### Attacker artifacts to include

- ciphertext and nonce;
- AES-GCM tag and AAD;
- round certificate and signature;
- packet metadata, timestamps, client pseudonym, and audit trace;
- pre- and post-round public global models if those are normally retained;
- encrypted database or object-store snapshot if backups are in scope;
- any public model architecture and training configuration;
- no destroyed key, no live key service, and no plaintext copy unless the threat model says otherwise.

### Attack metrics

For image reconstruction, use more than one metric. MedLeak defines recovery using thresholds such as **PSNR ≥20 dB and SSIM ≥0.90**, and also reports recovery rate and downstream task utility \[18\]. Medical-image inversion work likewise uses SSIM and MSE over 100 randomly sampled images \[19\]. For SDFL, define a successful breach as a reconstruction that satisfies a pre-registered quality criterion, for example:

- PSNR ≥20 dB **and** SSIM ≥0.90;
- plus a clinically meaningful downstream segmentation or classification score;
- while also reporting mean PSNR, SSIM, LPIPS or MSE, and the full distribution.

The primary target should be **0 high-quality reconstructions in 1,000 attacks per condition**. A low-quality artifact may still contain some structure, so report it instead of reducing the claim to “AES decryption failed.”

### What can be claimed

Defensible wording:

> Under the defined post-expiry threat model, no authenticated plaintext update or high-quality reconstruction was obtained in 0 of 1,000 independent attempts per tested condition after round-key destruction.

Too-strong wording:

> SDFL makes all past information unrecoverable.

The latter is not justified because the global model may already contain information learned from prior updates, and unauthorized copies made before expiry are outside ordinary key destruction. Federated unlearning literature makes the same distinction: deleting or invalidating historical updates does not remove their influence from an already-trained global model \[20\], \[21\].

## Temporal-window experiment

The correct value of $`T_r`$ cannot be chosen from 7,200 seconds alone. It should be derived from the empirical distribution of local training, serialization, upload, network, validation, and aggregation completion times.

### Recommended sweep

Use two complementary parameterizations:

- **Relative sweep:** 0.50, 0.75, 1.00, 1.25, and 1.50 times the observed p95 completion time.
- **Absolute sweep:** for example 60, 300, 900, 1,800, 3,600, and 7,200 seconds, but only after measuring whether local training actually fits inside these windows.

Add a clock-skew and network-jitter margin. The operating point should normally be near:

``` math
T_r = \text{p95 legitimate completion time} + \text{clock margin} + \text{network safety margin}.
```

### Target operating points

- **Minimum publishable:** legitimate completion at least 95%; late legitimate rejection no more than 5% \[E\].
- **Good journal:** completion at least 98%; late legitimate rejection no more than 2% \[E\].
- **Strong:** completion at least 99%; late legitimate rejection no more than 1% \[E\].

Report p50, p90, p95, and p99 completion time, round latency, expiry rejection, client dropout, and security-management overhead. The best graph is a Pareto curve with legitimate completion on the x-axis, rejection or security lifetime on the second axis, and round latency/overhead as annotated curves.

A two-hour window may be justified if local training is genuinely that slow, but it should not be presented as optimal without this sweep. A long window increases the time during which a captured update remains usable and weakens the temporal-security story.

## Ablation of the temporal mechanism

The ablation must separate ordinary encryption, integrity/freshness, expiry enforcement, and destruction. The most important missing control is **round-specific keys with key retention**. Without it, a reviewer cannot tell whether the benefit comes from key rotation or from destroying the key.

### Required ablation rows

| Row | Protection stack | Expected security behavior | What it isolates |
|:---|:---|:---|:---|
| A | Plain FedAvg | Plaintext update exposure; replay and cross-round reuse possible | Utility and unprotected security baseline |
| B | AES-GCM only, persistent key | Passive packet confidentiality; replay may still be accepted; post-expiry decryption remains possible while key exists | Encryption alone |
| C | AES-GCM plus certificate/AAD | Tampering and certificate mismatch rejected; same-round replay may still need a nonce ledger | Integrity and context binding |
| D | C plus expiry validation, key retained | Late updates rejected; retained ciphertext can still be decrypted by an authorized key holder | Temporal acceptance rule without destruction |
| E | C plus fresh round key, key retained | Round isolation; old rounds remain decryptable if old keys are retained | Key rotation without self-destruction |
| F | Full SDFL | Late, replayed, tampered, wrong-context, and post-destruction use rejected | Lifecycle destruction and invalidation |

For every row, report Dice, IoU, precision, recall, HD95 or ASSD, accepted timely updates, rejected attack attempts, decryption success after expiry, client encryption time, server aggregation time, bytes per round, and peak retained storage.

The convincing pattern is:

- Rows B–F have essentially the same utility as FedAvg when DP is disabled;
- Row C adds integrity/freshness but does not yet make old ciphertexts undecryptable;
- Row D rejects late submissions but still permits authorized retrospective decryption;
- Row E isolates round separation from destruction;
- Row F is the only row with post-destruction decryption failure and zero high-quality retrospective recovery.

## Robustness across random seeds

Three seeds are sufficient for a pilot, but **five seeds should be the minimum for the main journal utility tables**. Three-seed results can be retained for expensive exploratory experiments or clearly labelled limitations.

Use five seeds for:

- centralized, FedAvg, FedProx, and Full SDFL training;
- each principal DP operating point;
- the true unseen-center experiment;
- the temporal-window utility sweep if training is repeated;
- the main ablation table.

Security rejection tests do not need five full model-training seeds for every packet mutation. They need many independently generated keys, certificates, packet mutations, timestamps, and protocol instances. A practical design is 10 independent protocol setups and at least 1,000 randomized attack attempts per condition.

Recommended reporting:

- mean ± standard deviation across seeds;
- 95% bootstrap confidence intervals over patient-level predictions;
- center-wise macro mean and worst-center values;
- paired per-image comparisons for model ablations;
- effect sizes, not only p-values.

There is no universal variance cutoff, but these are useful engineering warnings:

- seed SD below 0.01 Dice: stable \[E\];
- 0.01–0.02: usually acceptable \[E\];
- 0.02–0.05: investigate \[E\];
- above 0.05: unstable and difficult to defend \[E\].

Do not perform a t-test on three seed means as the main evidence. Use paired bootstrap, permutation, or Wilcoxon tests on case-level predictions when the paired test set is appropriate. Correct for multiple comparisons if many metrics and ablations are tested.

## True unseen-hospital generalization

Hospital 2 is not an unseen center if it previously contributed training data. The evaluation must be redesigned so that the held-out hospital contributes no training updates, no model-selection information, and no threshold-tuning data.

For a first study, train on Hospital 1 and Hospital 3 and test on Hospital 2. This is useful but fragile because it contains only one unseen center. A stronger design uses leave-one-center-out evaluation across PolypGen or PolypDB-style data, or adds one external dataset such as Kvasir-SEG, PolypGen, or PolypDB with a pre-specified protocol \[2\], \[5\].

### Generalization target table

| Evaluation | Minimum publishable | Good journal target | Strong target | Evidence and interpretation |
|:---|---:|---:|---:|:---|
| Unseen-center Dice | $`\ge 0.60`$ \[E\] | 0.68–0.75 \[E\] | $`\ge 0.75–0.80`$ \[E\] | PolypGen unseen sequence results around 0.62–0.71 show that this is realistic for difficult video-like data \[2\]. |
| Unseen-center IoU | $`\ge 0.45`$ \[E\] | 0.52–0.62 \[E\] | $`\ge 0.62`$ \[E\] | Cross-dataset polyp IoU is often around 0.64–0.76 for stronger methods, but difficult cases are lower \[1\], \[13\]. |
| Seen-to-unseen degradation | $`\le 25\%`$ \[E\] | $`\le 20\%`$ \[E\] | $`\le 15\%`$ \[E\] | FedDG and cross-silo segmentation work show that domain shift should be measured explicitly rather than hidden in a pooled average \[8\], \[14\]. |
| Worst-center Dice | $`\ge 0.50`$ \[E\] | $`\ge 0.55–0.60`$ \[E\] | $`\ge 0.60`$ \[E\] | Multi-center benchmarks show that average scores can hide catastrophic site-specific failures \[22\], \[23\]. |
| Number of unseen centers | 1 with clear limitation \[R\] | 2 or leave-one-center-out \[E\] | 3 or more plus external dataset \[E\] | One held-out hospital is a minimum demonstration, not strong evidence of generalization. |

Use center-macro averaging so a large hospital cannot dominate the result. Report confidence intervals, sample counts, modality/device metadata, and failure cases. Include the fraction of cases with Dice ≤0.50 because challenge studies found substantial low-Dice tails even when average scores were high \[22\].

## Computational and communication overhead

Current encryption time of **0.0386 seconds per client** and aggregation time of **0.0835 seconds** appear small, but the denominator is missing. They must be reported as a percentage of the matched FedAvg client-training time and total round time.

Comparable systems span a wide range. Truhn et al. reported encryption/decryption overhead below 1% of total training time for a 3D brain-tumor segmentation task and below 5% for a smaller histopathology task \[24\]. Flamingo reported roughly **1.4×–1.7×** total-session overhead relative to non-private FedAvg in its benchmark setting \[25\]. Kaissis et al. reported approximately **2.91×** batch-time overhead for DP plus secure aggregation, showing that DP and cryptographic aggregation can dominate when the model or workload differs \[11\]. SAFE and Turbo-Aggregate show that protocol topology strongly affects scaling \[26\], \[27\].

### Systems target table

| Metric | Minimum publishable | Good journal target | Strong target | Interpretation |
|:---|---:|---:|---:|:---|
| Client encryption overhead | $`\le 15\%`$ of matched FedAvg client round \[E\] | $`\le 10\%`$ \[E\] | $`\le 5\%`$ \[E\] | Absolute seconds are not enough; report mean, p95, hardware, and payload size. |
| Server aggregation overhead | $`\le 15\%`$ of total round \[E\] | $`\le 10\%`$ \[E\] | $`\le 5\%`$ \[E\] | Current 0.0835 s may be negligible, but only relative measurement can establish this. |
| End-to-end SDFL runtime | $`\le 1.25\times`$ FedAvg \[E\] | $`\le 1.10\times`$ \[E\] | $`\le 1.05\times`$ \[E\] | Compare matched training, not centralized training alone. |
| Communication payload | $`\le 1.10\times`$ FedAvg \[E\] | $`\le 1.05\times`$ \[E\] | $`\le 1.02\times`$ \[E\] | AES-GCM and certificates should add little beyond the model update; secure aggregation/HE may be a separate comparison. |
| Peak retained update storage | Deleted or bounded after expiry \[E\] | No persistent plaintext; ciphertext lifetime logged \[E\] | Streaming or bounded $`O(d)`$ retention with verified deletion \[E\] | This is central to the temporal claim. Report crash, backup, and restart behavior. |
| Communication value | 79 MB/round must be normalized \[R\] | Payload ratio and total bytes reported \[E\] | Payload ratio near 1.0 plus WAN sensitivity \[E\] | At 100 Mbps, 79 MB is roughly 6.3 seconds for one idealized transfer; actual protocol time will be higher. |

Compare against:

- plain FedAvg;
- AES-GCM without temporal controls;
- the complete SDFL stack;
- at least one secure-aggregation or encrypted-FL reference implementation if the paper makes a cryptographic systems claim;
- centralized training only as a utility and compute reference, not as the main protocol baseline.

## Scalability

The proposed experiments with $`N=3,5,10,20`$ are appropriate for a cross-silo prototype, but they do not justify large-scale claims by themselves. Secure aggregation literature commonly tests hundreds or thousands of users and reports asymptotic behavior, while medical FL studies often use fewer real institutions \[25\], \[27\], \[28\], \[29\].

### Scalability target table

| Metric | Minimum publishable | Good journal target | Strong target | Required trend |
|:---|---:|---:|---:|:---|
| Per-client encryption time | Within 20% across N \[E\] | CV below 10% \[E\] | CV below 5% \[E\] | Per-client work should be approximately constant. |
| Server aggregation | Monotonic, approximately linear \[E\] | Linear fit with $`R^2\ge 0.95`$ \[E\] | No unexplained superlinear growth \[E\] | Report slope, intercept, and confidence bands. |
| Total communication | Linear in N \[L/E\] | Per-client payload stable within 5% \[E\] | Same plus WAN sensitivity \[E\] | Full-model communication naturally grows with N; this is not a flaw if clearly reported. |
| Parallel round time | No crash or timeout at N=20 \[E\] | p95 growth below 2× from N=3 to N=20 \[E\] | p95 growth below 1.5× \[E\] | State whether clients execute in parallel or serially. |
| Peak memory | No exhaustion at N=20 \[E\] | Streaming or bounded buffering \[E\] | Approximately O(d), independent of N \[E\] | Temporary ciphertext retention is especially relevant to self-destruction. |
| Security-management overhead | $`\le 15\%`$ \[E\] | $`\le 10\%`$ \[E\] | $`\le 5\%`$ \[E\] | Include certificate verification, key generation/destruction, deletion, and audit logging. |

For each N, report client CPU, server CPU, wall-clock round time, p50/p95 latency, bytes uploaded/downloaded, peak memory, key/certificate operations, deletion time, and failure recovery time. A simple linear trend with uncertainty is more credible than a single speedup number.

## Overall paper-level target matrix

| Metric | Current | Minimum publishable | Good journal target | Strong target |
|:---|---:|---:|---:|---:|
| Centralized Dice | 0.7937 | 0.75–0.80 | 0.80–0.86 | $`\ge 0.86`$ |
| FedAvg Dice | 0.7712 | $`\ge 0.70`$ | 0.75–0.80 | $`\ge 0.80`$ |
| Full SDFL Dice | 0.4145 ID | 0.55–0.60 | 0.65–0.72 | 0.72–0.78 |
| Utility retention vs. FedAvg | 53.8% | 70–80% | 85–92% | $`\ge 92\%`$ |
| Full SDFL IoU | 0.2994 | 0.40–0.50 | 0.50–0.60 | $`\ge 0.60`$ |
| Cumulative epsilon | 2.772 approximate | Exact, $`\le 8`$ | Exact, $`\le 5`$ | Exact, $`\le 2–3`$ |
| Delta | Not specified here | $`\le 10^{-4}`$ justified | $`\le 10^{-5}`$ | $`\le 10^{-6}`$ where feasible |
| Post-expiry attack success | 0%, protocol size unclear | 0/1,000 per primary condition | 0/5,000 | 0/10,000 plus formal argument |
| Replay success | Not measured | 0/1,000 | 0/5,000 | 0/10,000 |
| Certificate tampering success | Not measured | 0/1,000 | 0/5,000 | 0/10,000 |
| Cross-round attack success | Not measured | 0/1,000 | 0/5,000 | 0/10,000 |
| Legitimate completion | Not measured | $`\ge 95\%`$ | $`\ge 98\%`$ | $`\ge 99\%`$ |
| Late legitimate rejection | Not measured | $`\le 5\%`$ | $`\le 2\%`$ | $`\le 1\%`$ |
| Encryption overhead | 0.0386 s/client | $`\le 15\%`$ of FedAvg round | $`\le 10\%`$ | $`\le 5\%`$ |
| Aggregation overhead | 0.0835 s | $`\le 15\%`$ of round | $`\le 10\%`$ | $`\le 5\%`$ |
| Communication | ~79 MB/round | $`\le 1.10\times`$ FedAvg | $`\le 1.05\times`$ | $`\le 1.02\times`$ |
| Unseen-center Dice | Not measured | $`\ge 0.60`$ | 0.68–0.75 | $`\ge 0.75–0.80`$ |
| Seed variability | Not measured | SD $`\le 0.03`$ | SD $`\le 0.02`$ | SD $`\le 0.01`$ |

The Dice, epsilon, overhead, and variance values in this table are target heuristics, not literature laws. The directly literature-supported conclusions are narrower: ordinary federated segmentation often stays near centralized performance; DP can cause moderate to severe utility loss depending on privacy unit and client count; cross-center polyp performance can fall into the 0.60–0.75 range; and cryptographic papers expect formal threat models plus explicit computation and communication analysis \[2\], \[8\], \[9\], \[10\], \[12\], \[16\].

## Must-have, should-have, and nice-to-have experiments

### Must-have before submission

- Recompute cumulative DP with a documented accountant and explicit privacy unit.
- Add the complete six-row temporal ablation, including round-key retention without destruction.
- Implement certificate-bound AES-GCM AAD, replay protection, model-hash binding, and cross-round checks.
- Run at least 1,000 independent attempts per primary attack condition and report exact confidence bounds.
- Run the retrospective breach experiment with a written attacker artifact list and pre-registered reconstruction thresholds.
- Add five-seed utility experiments for FedAvg, the best non-private baseline, and Full SDFL.
- Perform a true unseen-center evaluation with no training or tuning exposure to the held-out center.
- Normalize encryption, aggregation, communication, memory, and total-round overhead against FedAvg.
- Report precision, recall, and a boundary metric in addition to Dice and IoU.

### Should-have

- Sweep $`T_r`$ using p95 completion time and clock/network margins.
- Report center-wise macro means, worst-center results, and low-Dice failure fractions.
- Add one external dataset or leave-one-center-out evaluation.
- Test crash/restart, backup snapshot, duplicate packet, delayed packet, and key-destruction recovery paths.
- Compare against one secure-aggregation or encrypted-FL implementation with matched model size.
- Include a privacy–utility curve over several exact epsilon values.

### Nice-to-have

- Client counts beyond 20 or a validated simulator for 50–100 clients.
- Formal proof or machine-checkable argument for certificate binding and key lifecycle.
- Independent third-party reproduction of the protocol tests.
- Membership-inference or gradient-inversion evaluation on the surviving global model, clearly separated from post-expiry ciphertext decryption.
- Failure-detection AUC improvement. The current AUC of 0.5052 is approximately random and should remain future work rather than a core result.

## Red flags that should delay submission

- Full SDFL remains below 0.50 on the ordinary in-domain test and no less-private operating point reaches useful utility.
- The paper claims temporal privacy from key deletion but retains decryptable backups, long-term keys, plaintext buffers, or process snapshots.
- Epsilon is reported from one round, from a server-side approximation, or without a clear adjacency definition.
- The paper calls SDFL “federated unlearning” or “removal of learned information.” Key destruction does not erase information already absorbed by the global model \[20\], \[21\].
- “0% attack success” is based on only five tests, one key, one round, or a weak attacker with incomplete artifacts.
- Replay, certificate tampering, wrong-key, or cross-round substitution are not tested separately.
- Hospital 2 is called unseen after it participated in training.
- Results are reported only as pooled averages and hide a failing center or a large low-Dice tail.
- Runtime is compared only with centralized training or only as absolute seconds.
- The agentic or uncertainty module is allowed to control cryptographic validity, expiry, or key destruction without a deterministic fallback.

## Green flags that would make the paper convincing

- Full SDFL retains at least 85% of FedAvg Dice at an exact cumulative epsilon in the 2–5 range, or the paper clearly presents a lower-utility stress point alongside a useful operating point.
- AES-GCM, certificate binding, expiry validation, and destruction are isolated in a clean ablation.
- Every primary attack has 0 successes in at least 1,000 attempts, with confidence bounds and attack artifacts specified.
- Timely updates are accepted at least 98–99% of the time while late updates are rejected at least 98–99% of the time.
- Post-destruction decryption fails and retrospective reconstruction fails under the declared threat model, while the global model remains available for later rounds.
- A true unseen-center result remains above roughly 0.68 Dice with no catastrophic center failure.
- Five seeds, center-wise confidence intervals, and paired statistical comparisons show that the result is not a single-run artifact.
- Full SDFL adds no more than about 10% end-to-end runtime and little communication beyond the update payload.
- The paper explicitly says what SDFL does not protect: plaintext captured before expiry, unauthorized local copies, information already absorbed by the global model, and threats outside the key-erasure model.

## Smallest credible final experimental matrix

| Block | Experiments | Minimum design |
|:---|:---|:---|
| Utility | Centralized, FedAvg, FedProx, AES-only, certificate/AAD, expiry-with-retained-key, Full SDFL | Same split, same backbone, five seeds; Dice, IoU, precision, recall, HD95/ASSD. |
| DP | Three or four exact epsilon operating points | Cumulative accountant over all rounds; report $`\epsilon`$, $`\delta`$, privacy unit, and attack metrics. |
| Security | Timely, expired, replay, tampered certificate, wrong key, cross-round, post-destruction | At least 1,000 randomized attempts per condition, across five rounds and multiple protocol seeds. |
| Retrospective breach | Captured ciphertext and metadata, no destroyed key | 1,000 or more attempts per attack setting; PSNR/SSIM/recovery rate/downstream utility. |
| Temporal window | Six absolute or percentile-based $`T_r`$ values | Completion, late rejection, p50/p95 latency, overhead, and security lifetime. |
| Generalization | True held-out hospital plus external or leave-one-center-out test | Center-macro Dice/IoU, worst-center score, degradation, and low-Dice fraction. |
| Systems | N = 3, 5, 10, 20 | Five timing repetitions; client/server CPU, wall-clock, bytes, memory, key lifecycle, and deletion latency. |

This matrix is the smallest set that can credibly support the claim that SDFL contributes a protocol-enforced temporal security boundary rather than merely adding ordinary encryption to a low-utility segmentation model.

## Final positioning

The paper should position the contribution as **temporal invalidation of federated update artifacts**. Encryption protects confidentiality while the packet is protected; certificates and AAD provide authenticity and context binding; replay protection provides freshness; expiry rejects late protocol use; key destruction and artifact deletion reduce authorized post-expiry recoverability. These are distinct properties.

The paper should not claim that SDFL improves segmentation architecture, achieves certified federated unlearning, erases information already present in the global model, or guarantees physical deletion of every unauthorized copy. A strong and defensible claim is:

> SDFL adds a protocol-enforced temporal lifecycle to federated model updates. Under the defined threat model, updates are accepted only within a signed round window, stale or mismatched artifacts are rejected, and post-expiry decryption or high-quality reconstruction fails after destruction of the round-specific cryptographic context.

That claim can be journal-worthy even without state-of-the-art Dice, but only if the temporal-security evidence is rigorous and the utility loss is brought out of the current 53.8% retention regime or clearly presented as a controlled stress-test trade-off.

---

## References

\[1\] D. Jha *et al.*, “A Comprehensive Study on Colorectal Polyp Segmentation With ResUNet++, Conditional Random Field and Test-Time Augmentation,” *IEEE Journal of Biomedical and Health Informatics*, vol. 25, pp. 2029–2040, Jan. 2021, doi: [10.1109/JBHI.2021.3049304](https://doi.org/10.1109/JBHI.2021.3049304).

\[2\] S. Ali *et al.*, “A multi-centre polyp detection and segmentation dataset for generalisability assessment,” *Scientific Data*, vol. 10, Jun. 2021, doi: [10.1038/s41597-023-01981-y](https://doi.org/10.1038/s41597-023-01981-y).

\[3\] H. Pan, D. Jha, K. Biswas, and U. Bagci, “Frequency-Based Federated Domain Generalization for Polyp Segmentation,” *ICASSP 2025 - 2025 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*, pp. 1–5, Oct. 2024, doi: [10.1109/ICASSP49660.2025.10889662](https://doi.org/10.1109/ICASSP49660.2025.10889662).

\[4\] K. Fan, C. Xu, X. Cao, K. Jiao, and W. Mo, “Tri-branch feature pyramid network based on federated particle swarm optimization for polyp segmentation.” *Mathematical biosciences and engineering : MBE*, vol. 21 1, pp. 1610–1624, Jan. 2024, doi: [10.3934/mbe.2024070](https://doi.org/10.3934/mbe.2024070).

\[5\] D. Jha *et al.*, “PolypDB: A Curated Multi-Center Dataset for Development of AI Algorithms in Colonoscopy,” *ArXiv*, vol. abs/2409.00045, Aug. 2024, doi: [10.48550/arXiv.2409.00045](https://doi.org/10.48550/arXiv.2409.00045).

\[6\] G. Skorupko *et al.*, “Federated nnU-Net for privacy-preserving medical image segmentation,” *Scientific Reports*, vol. 15, Mar. 2025, doi: [10.1038/s41598-025-22239-0](https://doi.org/10.1038/s41598-025-22239-0).

\[7\] M. Manthe, S. Duffner, and C. Lartizien, “Federated brain tumor segmentation: An extensive benchmark,” *Medical image analysis*, vol. 97, pp. 103270, Jul. 2024, doi: [10.1016/j.media.2024.103270](https://doi.org/10.1016/j.media.2024.103270).

\[8\] A. Xu *et al.*, “Closing the Generalization Gap of Cross-silo Federated Medical Image Segmentation,” *2022 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 20834–20843, Mar. 2022, doi: [10.1109/CVPR52688.2022.02020](https://doi.org/10.1109/CVPR52688.2022.02020).

\[9\] A. Ziller *et al.*, “Differentially private federated deep learning for multi-site medical image segmentation,” *ArXiv*, vol. abs/2107.02586, Jul. 2021.

\[10\] M. Adnan, S. Kalra, J. C. Cresswell, G. W. Taylor, and H. Tizhoosh, “Federated learning and differential privacy for medical image analysis,” *Scientific Reports*, vol. 12, Nov. 2021, doi: [10.1038/s41598-022-05539-7](https://doi.org/10.1038/s41598-022-05539-7).

\[11\] G. Kaissis *et al.*, “End-to-end privacy preserving deep learning on multi-institutional medical imaging,” *Nature Machine Intelligence*, vol. 3, pp. 473–484, May 2021, doi: [10.1038/s42256-021-00337-8](https://doi.org/10.1038/s42256-021-00337-8).

\[12\] M. Jiang, Y. Zhong, A. Le, X. Li, and Q. Dou, “Client-Level Differential Privacy via Adaptive Intermediary in Federated Medical Imaging,” *ArXiv*, vol. abs/2307.12542, Jul. 2023, doi: [10.48550/arXiv.2307.12542](https://doi.org/10.48550/arXiv.2307.12542).

\[13\] Y. Tudela *et al.*, “A complete benchmark for polyp detection, segmentation and classification in colonoscopy images,” *Frontiers in Oncology*, vol. 14, Sep. 2024, doi: [10.3389/fonc.2024.1417862](https://doi.org/10.3389/fonc.2024.1417862).

\[14\] Q. Liu, C. Chen, J. Qin, Q. Dou, and P. Heng, “FedDG: Federated Domain Generalization on Medical Image Segmentation via Episodic Learning in Continuous Frequency Space,” *2021 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 1013–1023, Mar. 2021, doi: [10.1109/CVPR46437.2021.00107](https://doi.org/10.1109/CVPR46437.2021.00107).

\[15\] S. Pfohl, A. M. Dai, and K. Heller, “Federated and Differentially Private Learning for Electronic Health Records,” *ArXiv*, vol. abs/1911.05861, Nov. 2019.

\[16\] M. Mansouri, M. Önen, W. B. Jaballah, and M. Conti, “SoK: Secure Aggregation Based on Cryptographic Schemes for Federated Learning,” *Proc. Priv. Enhancing Technol.*, vol. 2023, pp. 140–157, Jan. 2023, doi: [10.56553/popets-2023-0009](https://doi.org/10.56553/popets-2023-0009).

\[17\] D. Pasquini, D. Francati, and G. Ateniese, “Eluding Secure Aggregation in Federated Learning via Model Inconsistency,” *Proceedings of the 2022 ACM SIGSAC Conference on Computer and Communications Security*, Nov. 2021, doi: [10.1145/3548606.3560557](https://doi.org/10.1145/3548606.3560557).

\[18\] S. Shi *et al.*, *MedLeak: Multimodal Medical Data Leakage in Secure Federated Learning with Crafted Models*. 2024, pp. 245–256. doi: [10.1145/3721201.3721375](https://doi.org/10.1145/3721201.3721375).

\[19\] B. Das, M. Amini, and Y. Wu, “Privacy Risks Analysis and Mitigation in Federated Learning for Medical Images,” *2023 IEEE International Conference on Bioinformatics and Biomedicine (BIBM)*, pp. 1870–1873, Nov. 2023, doi: [10.1109/BIBM58861.2023.10385829](https://doi.org/10.1109/BIBM58861.2023.10385829).

\[20\] Y. Liu, L. Xu, X. Yuan, C. Wang, and B. Li, “The Right to be Forgotten in Federated Learning: An Efficient Realization with Rapid Retraining,” *IEEE INFOCOM 2022 - IEEE Conference on Computer Communications*, pp. 1749–1758, Mar. 2022, doi: [10.1109/INFOCOM48880.2022.9796721](https://doi.org/10.1109/INFOCOM48880.2022.9796721).

\[21\] N. Romandini, A. Mora, C. Mazzocca, R. Montanari, and P. Bellavista, “Federated Unlearning: A Survey on Methods, Design Guidelines, and Evaluation Metrics,” *IEEE Transactions on Neural Networks and Learning Systems*, vol. 36, pp. 11697–11717, Jan. 2024, doi: [10.1109/TNNLS.2024.3478334](https://doi.org/10.1109/TNNLS.2024.3478334).

\[22\] S. Ali *et al.*, “Assessing generalisability of deep learning-based polyp detection and segmentation methods through a computer vision challenge,” *Scientific Reports*, vol. 14, Feb. 2022, doi: [10.1038/s41598-024-52063-x](https://doi.org/10.1038/s41598-024-52063-x).

\[23\] M. Zenk *et al.*, “Towards fair decentralized benchmarking of healthcare AI algorithms with the Federated Tumor Segmentation (FeTS) challenge,” *Nature Communications*, vol. 16, Jul. 2025, doi: [10.1038/s41467-025-60466-1](https://doi.org/10.1038/s41467-025-60466-1).

\[24\] D. Truhn *et al.*, “Encrypted federated learning for secure decentralized collaboration in cancer image analysis,” *Medical Image Analysis*, vol. 92, Jul. 2022, doi: [10.1016/j.media.2023.103059](https://doi.org/10.1016/j.media.2023.103059).

\[25\] Y. Ma, J. Woods, S. Angel, A. Polychroniadou, and T. Rabin, “Flamingo: Multi-Round Single-Server Secure Aggregation with Applications to Private Federated Learning,” *2023 IEEE Symposium on Security and Privacy (SP)*, pp. 477–496, May 2023, doi: [10.1109/SP46215.2023.10179434](https://doi.org/10.1109/SP46215.2023.10179434).

\[26\] T. Sandholm, S. Mukherjee, and B. A. Huberman, “SAFE: Secure Aggregation with Failover and Encryption,” *ACM Transactions on Modeling and Performance Evaluation of Computing Systems*, vol. 10, pp. 1–28, Aug. 2021, doi: [10.1145/3716630](https://doi.org/10.1145/3716630).

\[27\] J. So, B. Guler, and A. Avestimehr, “Turbo-Aggregate: Breaking the Quadratic Aggregation Barrier in Secure Federated Learning,” *IEEE Journal on Selected Areas in Information Theory*, vol. 2, pp. 479–489, Feb. 2020, doi: [10.1109/JSAIT.2021.3054610](https://doi.org/10.1109/JSAIT.2021.3054610).

\[28\] N. Sultan *et al.*, *Setup Once, Secure Always: A Single-Setup Secure Federated Learning Aggregation Protocol with Forward and Backward Secrecy for Dynamic Users*. 2025. doi: [10.1145/3779208.3785414](https://doi.org/10.1145/3779208.3785414).

\[29\] T. Eltaras, F. Sabry, W. Labda, K. Alzoubi, and Q. Ahmedeltaras, “Efficient Verifiable Protocol for Privacy-Preserving Aggregation in Federated Learning,” *IEEE Transactions on Information Forensics and Security*, vol. 18, pp. 2977–2990, 2023, doi: [10.1109/TIFS.2023.3273914](https://doi.org/10.1109/TIFS.2023.3273914).
