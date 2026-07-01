# SDFL literature survey and roadmap

##### [**Undermind**](https://undermind.ai)

---


## Table of Contents

- [SDFL literature survey and roadmap](#sdfl-literature-survey-and-roadmap)
  - [SDFL concept](#sdfl-concept)
    - [Mentor summary](#mentor-summary)
    - [How $`T_r`$ is set, enforced, and verified](#how-t_r-is-set-enforced-and-verified)
    - [Examiner-facing clarification](#examiner-facing-clarification)
  - [Literature landscape](#literature-landscape)
    - [What is already applied separately and what is not yet combined](#what-is-already-applied-separately-and-what-is-not-yet-combined)
    - [Core strands in the literature](#core-strands-in-the-literature)
    - [What the colonoscopy literature shows](#what-the-colonoscopy-literature-shows)
    - [What the FL literature shows](#what-the-fl-literature-shows)
    - [What the privacy literature shows](#what-the-privacy-literature-shows)
  - [Research gaps](#research-gaps)
    - [Gap table](#gap-table)
    - [Five priority gaps](#five-priority-gaps)
  - [Patent-oriented novelty mapping](#patent-oriented-novelty-mapping)
    - [Novelty checklist](#novelty-checklist)
    - [Components that appear most defensible as a patent-oriented package](#components-that-appear-most-defensible-as-a-patent-oriented-package)
  - [Recommended implementation roadmap](#recommended-implementation-roadmap)
    - [Threat model](#threat-model)
    - [Model choice](#model-choice)
    - [Federated training strategy](#federated-training-strategy)
    - [Privacy stack](#privacy-stack)
    - [Round lifecycle](#round-lifecycle)
    - [Evaluation plan](#evaluation-plan)
    - [Minimum baseline set](#minimum-baseline-set)
  - [Working thesis for the project](#working-thesis-for-the-project)
  - [Inventive core](#inventive-core)
    - [Narrow claim summary](#narrow-claim-summary)
  - [References](#references)

# SDFL literature survey and roadmap

Self-Destructing Federated Learning for colorectal polyp detection sits at the intersection of three literatures that have mostly evolved apart: centralized colonoscopy segmentation, privacy-preserving federated learning for medical imaging, and cryptographic or deletion-oriented protection of model updates. The literature now shows that federated learning for polyp segmentation is feasible (Stelter et al. 2024; Fan et al. 2024; H. Pan et al. 2024; Chen et al. 2025), but the strongest privacy controls still come from work outside gastrointestinal imaging (Kaissis et al. 2021; Truhn et al. 2022; R. Xu et al. 2024; Hu and Li 2025; Pati et al. 2024). The practical novelty space is therefore not a new segmentation model alone. It is the construction of an end-to-end colorectal FL system that treats model updates as short-lived sensitive objects rather than as benign training byproducts (Pati et al. 2024; Pasquini et al. 2021; Shi et al. 2024; G. Liu et al. 2021).

This report synthesizes the current literature for a project on Self-Destructing Federated Learning applied to colorectal polyp segmentation with Kvasir-SEG and related colonoscopy datasets. The emphasis is on research gaps that are technically meaningful, useful for a student research paper, and supportive of a patent-oriented novelty position.

## SDFL concept

Self-Destructing Federated Learning introduces **temporal privacy** into healthcare federated learning. The key idea is that privacy protection should not stop at keeping raw data local. Model updates, gradients, and their enabling key material should have a limited useful lifetime. In the refined version of the concept, each federated round is bound to an explicit expiry timestamp $`T_r`$. Updates are accepted and usable only inside that round window, and the round-specific decryption context is destroyed once aggregation closes.

This shifts the security question from **can an attacker access updates?** to **what remains useful even if access occurs later?** That shift is motivated by the medical FL literature showing that gradients, aggregated updates, and stored intermediate artifacts can still expose sensitive information through inversion or inference attacks (Pati et al. 2024; Pasquini et al. 2021; Shi et al. 2024; Hatamizadeh et al. 2022). The timestamp mechanism is the practical step that turns temporal privacy from a general idea into a concrete system rule: retain the global model, but let the per-round contribution path expire. \## What is borrowed from prior papers and what is new here

The strongest way to explain SDFL to a supervisor or reviewer is to separate **borrowed building blocks** from the **new system step**. The literature already supports the need for secure medical FL, the reality of aggregate-level leakage, and the existence of revocation or unlearning after training (Kaissis et al. 2021; Pasquini et al. 2021; Shi et al. 2024; Yang Liu et al. 2019; G. Liu et al. 2021). What the reviewed set does not yet provide is a colorectal FL pipeline in which each round has a clear expiry timestamp and update usability ends automatically when that timestamp passes.

| System element | Source paper title | What the paper already contributes | Status in SDFL |
|:---|:---|:---|:---|
| End-to-end medical FL with privacy controls | *End-to-end privacy preserving deep learning on multi-institutional medical imaging* (Kaissis et al. 2021) | Shows that federated medical imaging can be combined with differential privacy, secure aggregation, and encrypted inference in one practical stack | Paper-derived foundation |
| Secure aggregation is not enough by itself | *Eluding Secure Aggregation in Federated Learning via Model Inconsistency* (Pasquini et al. 2021) | Shows that a malicious server can make the final aggregate leak user-level information even when secure aggregation is present | Paper-derived threat motivation |
| Aggregated updates can still reveal medical data | *MedLeak: Multimodal Medical Data Leakage in Secure Federated Learning with Crafted Models* (Shi et al. 2024) | Shows that private medical images and text can be recovered from aggregated updates under a crafted attack setting | Paper-derived threat motivation |
| Round independence and secrecy in secure aggregation | *Setup Once, Secure Always: A Single-Setup Secure Federated Learning Aggregation Protocol with Forward and Backward Secrecy for Dynamic Users* (Sultan et al. 2025) | Gives forward and backward secrecy with fresh round masking, but does not make update validity explicitly timestamp-bound or automatically delete round artifacts after expiry | Paper-derived partial mechanism |
| Participant revocation and removal of old influence | *Revocable Federated Learning: A Benchmark of Federated Forest* (Yang Liu et al. 2019) | Treats revocation as removal of a participant’s learned influence after an explicit revocation event | Paper-derived deletion literature |
| Federated unlearning after training | *FedEraser: Enabling Efficient Client-Level Data Removal from Federated Learning Models* (G. Liu et al. 2021) | Removes a client’s influence from the trained model by using retained update history | Paper-derived deletion literature |
| Secure retention as a competing design choice | *Secure Stateful Aggregation: A Practical Protocol with Applications in Differentially-Private Federated Learning* (Ball et al. 2024) | Shows that some high-utility private FL methods rely on persistent secure aggregate storage rather than deletion | Paper-derived counterpoint |
| Attention-based segmentation backbone | *FCN-Transformer Feature Fusion for Polyp Segmentation* (Sanderson and Matuszewski 2022) and *Efficient colorectal polyp segmentation using wavelet transformation and AdaptUNet: A hybrid U-Net* (Rajasekar et al. 2024) | Show that transformer fusion and attention-enhanced segmentation improve polyp delineation and boundary quality | Paper-derived model choice |
| Uncertainty estimation for trustworthy medical segmentation and FL | *Trustworthy clinical AI solutions: a unified review of uncertainty quantification in deep learning models for medical image analysis* (Lambert et al. 2022) and *Privacy Preserving Federated Learning in Medical Imaging with Uncertainty Estimation* (Koutsoubis et al. 2024) | Show that uncertainty can support quality control, failure detection, and human review, but adds evaluation and compute burden | Paper-derived validation layer |
| Timestamp-bound update validity with automatic expiry | No direct prior paper found in the reviewed colorectal FL set | Defines a round expiry timestamp $`T_r`$, accepts updates only within that window, then deletes round-specific decryption material and cached update artifacts while retaining the global model | Gap-motivated and novel system step |

### Mentor summary

The proposed architecture does **not** claim that encryption, secure aggregation, revocation, or unlearning are individually new. Those are borrowed. The novel claim is narrower and clearer: **federated colorectal training rounds should have a built-in expiry timestamp, and once that timestamp passes, the system should automatically remove the cryptographic and storage conditions that make old updates reusable**. That claim is gap-motivated by the leakage papers (Pasquini et al. 2021; Shi et al. 2024), informed by secure aggregation design (Sultan et al. 2025), and distinguished from revocation or unlearning work (Yang Liu et al. 2019; G. Liu et al. 2021).

A remaining systems issue is that an expiry timestamp is too weak if it exists only as a local rule. A client could ignore it. The design therefore needs protocol-level enforcement. The cleanest formulation is a **coordinator-signed round certificate** that binds the round identifier, model hash, participant set, key-context identifier, and expiry timestamp $`T_r`$. A submitted update is valid only if it is cryptographically tied to that certificate and reaches the aggregator before $`T_r`$. After $`T_r`$, the aggregator rejects late submissions and the round decryption context is erased.

### How $`T_r`$ is set, enforced, and verified

| Design question | Proposed mechanism | Why it matters |
|:---|:---|:---|
| How is $`T_r`$ set | The coordinator defines $`T_r`$ at round creation and includes it in a signed round certificate | Makes the expiry rule global rather than local to each hospital |
| How is $`T_r`$ enforced | The aggregator verifies the certificate and rejects uploads that arrive after $`T_r`$ | Prevents a hospital from extending round validity by local choice |
| How is round reuse blocked | Each update is bound to the round certificate, model hash, and round-specific key context | Prevents replay of stale or cross-round artifacts |
| How is expiry made effective | At $`T_r`$, the server deletes round decryption material and cached ciphertexts, while clients delete local residual update buffers on a best-effort basis | Turns time expiry into loss of update usability |
| How is expiry verified | Round open and round close events are written to an append-only audit log | Lets the system prove that the round was closed and key material was retired |

### Examiner-facing clarification

The strongest defensible claim is **not** that every client device is physically forced to forget. A hospital may still keep an unauthorized local copy outside the protocol. The stronger and more credible claim is narrower: after $`T_r`$, the system will not accept a late update as a valid round contribution, and retained round ciphertexts cannot be decrypted through the ordinary protocol because the round context has expired. This keeps the invention grounded as a protocol-enforced expiry mechanism rather than an overbroad deletion claim.

## Literature landscape

### What is already applied separately and what is not yet combined

| Already applied separately | Not yet found as one colorectal FL system |
|:---|:---|
| Polyp segmentation on Kvasir-SEG and related datasets (Jha, Ali, et al. 2021; Jha, Smedsrud, et al. 2021; Sanderson and Matuszewski 2022; Rajasekar et al. 2024; Ahamed et al. 2024) | Temporal key destruction in colorectal FL |
| Federated polyp segmentation (Stelter et al. 2024; Fan et al. 2024; H. Pan et al. 2024; Chen et al. 2025; Zhang et al. 2025) | Automatic post-aggregation invalidation of updates |
| DP, secure aggregation, or HE in medical FL (Kaissis et al. 2021; Truhn et al. 2022; R. Xu et al. 2024; Hu and Li 2025) | One stack combining colorectal FL, temporal privacy, and sanitization |
| DICOM and image de-identification (Kondylakis et al. 2024; Rempe et al. 2024; Rutherford et al. 2021; Shahid et al. 2022) | Sanitization integrated into a full temporal-FL lifecycle |
| Federated unlearning (G. Liu et al. 2021; Deng et al. 2024) | Immediate round closure destruction instead of later forgetting |
| Timed or delay-based cryptography (Medley et al. 2023; Yuan et al. 2024; Sultan et al. 2025) | Timed cryptography used as a colorectal FL update-lifecycle mechanism |

### Core strands in the literature

| Strand | What the literature already does | Representative papers |
|:---|:---|:---|
| Polyp segmentation | Improves Dice, IoU, speed, and boundary quality on Kvasir-SEG and related datasets | (Jha, Ali, et al. 2021), (Jha, Smedsrud, et al. 2021), (Sanderson and Matuszewski 2022), (Rajasekar et al. 2024), (Ahamed et al. 2024), (Dumitru et al. 2023), (Yue et al. 2024) |
| Federated medical imaging | Enables cross-site training under non-IID data and limited trust | (Kaissis et al. 2021), (Adnan et al. 2021), (Truhn et al. 2022), (Skorupko et al. 2025), (A. Xu et al. 2022), (Hosseini et al. 2023) |
| GI and polyp FL | Applies FL directly to polyp segmentation and domain generalization | (Fan et al. 2024), (H. Pan et al. 2024), (Stelter et al. 2024), (Chen et al. 2025), (Zhang et al. 2025) |
| Privacy hardening in FL | Adds DP, HE, secure aggregation, fairness, or poisoning defense | (Kaissis et al. 2021), (L. Pan et al. 2024), (R. Xu et al. 2024), (Hu and Li 2025), (Z. Ma et al. 2022), (Pati et al. 2024) |
| De-identification and deletion | Handles DICOM sanitization, metadata leakage, or federated unlearning | (Kondylakis et al. 2024), (Rempe et al. 2024), (Rutherford et al. 2021), (Shahid et al. 2022), (G. Liu et al. 2021), (Deng et al. 2024) |
| Time-bound cryptography | Studies timed-release, delay-based, or forward/backward secure primitives | (Medley et al. 2023), (Yuan et al. 2024), (Sultan et al. 2025) |

### What the colonoscopy literature shows

Kvasir-SEG remains the most common benchmark in colorectal polyp segmentation (Jha, Ali, et al. 2021; Jha, Smedsrud, et al. 2021; Sanderson and Matuszewski 2022; Ahamed et al. 2024). This literature is strong on architectural refinement. ResUNet++ with CRF and test-time augmentation improved performance and specifically evaluated sessile or flat polyps (Jha, Smedsrud, et al. 2021). FCBFormer improved full-resolution prediction by fusing a convolutional branch and a transformer branch (Sanderson and Matuszewski 2022). AdaptUNet used wavelet features and attention to improve robustness across datasets (Rajasekar et al. 2024). DUCK-Net and BRNet both target the recurring problem of ambiguous boundaries and low-contrast lesions (Dumitru et al. 2023; Yue et al. 2024).

The central weakness of this line of work is not lack of model creativity. It is weak evidence of hospital-level generalization. Several papers perform cross-dataset tests, but most of the field still treats Kvasir-SEG as the main proving ground, even though multi-centre variability is the practical bottleneck in deployment (Bhattacharya et al. 2022; Jha, Smedsrud, et al. 2021; Ali et al. 2021; Jha et al. 2024). PolypGen was created precisely because single-centre or narrow-distribution benchmarks do not test generalizability hard enough (Ali et al. 2021). PolypDB extends this point with a multi-centre, multi-modality benchmark and explicit federated settings (Jha et al. 2024).

### What the FL literature shows

Federated learning in medical imaging is already mature enough to support deployment-oriented design decisions. PriMIA combined federated learning with differential privacy, secure aggregation, and encrypted inference, showing that a practical multi-institution privacy stack is possible (Kaissis et al. 2021). Differentially private FL for histopathology also showed that useful performance can remain close to centralized training at moderate privacy budgets, though domain shift remains a serious problem (Adnan et al. 2021). Encrypted FL in cancer imaging demonstrated that homomorphic protection of updates can be added with relatively modest overhead in some settings (Truhn et al. 2022). FednnU-Net showed that strong segmentation backbones can be adapted into FL settings, but also acknowledged that standard FL remains vulnerable to inversion and membership inference risks (Skorupko et al. 2025).

For non-IID segmentation, the literature is even clearer. FedSM directly targets the generalization gap between cross-silo FL and centralized training (A. Xu et al. 2022). Prop-FFL addresses fairness across hospitals (Hosseini et al. 2023). In polyp segmentation itself, newer GI papers focus on the same issue from different angles: federated particle swarm optimization (Fan et al. 2024), frequency-based federated domain generalization (H. Pan et al. 2024), and adaptive aggregation (Zhang et al. 2025). The trend is consistent: the real engineering problem is not whether FL can be used, but how to make it stable and generalizable under heterogeneous clinical distributions.

### What the privacy literature shows

The privacy literature makes a critical point that matters for SDFL: FL alone does not make model updates safe. Surveys in healthcare FL repeatedly note that gradients and model updates can leak information about local training data (Pati et al. 2024; Ghosh et al. 2026). PriMIA reduced leakage risk with DP and secure aggregation (Kaissis et al. 2021), and HE-based approaches protect updates during aggregation (Truhn et al. 2022; Hu and Li 2025; J. Ma et al. 2021; R. Xu et al. 2024). But secure aggregation is not a complete answer. Protocol misuse and aggregate-level attacks can still expose sensitive information (Pasquini et al. 2021; Shi et al. 2024). Attack papers continue to improve inversion quality and show that medical imaging is still at risk (Hatamizadeh et al. 2022; Wei et al. 2025).

This motivates the central SDFL claim: privacy should cover **before leakage, during training, and after breach**. Existing FL systems mainly address the first two. SDFL extends the design target to post-breach safety by treating updates and keys as expiring objects rather than durable assets. The literature already knows how to hide updates during transit or aggregation (R. Xu et al. 2024; Hu and Li 2025), and it also knows how to perform post hoc deletion or unlearning after training (G. Liu et al. 2021; Yi Liu et al. 2022; Halimi et al. 2022; Deng et al. 2024). What it does not yet combine is automatic, round-level invalidation of updates after aggregation.

## Research gaps

### Gap table

| Gap | Existing work | What is still missing | SDFL direction |
|:---|:---|:---|:---|
| Cross-centre polyp robustness is weak | Strong centralized models and recent polyp FL studies (Jha, Smedsrud, et al. 2021; Sanderson and Matuszewski 2022; Stelter et al. 2024; H. Pan et al. 2024) | Better handling of unseen hospitals, modalities, and devices | FL with explicit domain generalization and multi-centre validation |
| Small flat and camouflaged polyp handling remains fragile | Sessile-flat analysis and boundary models exist (Jha, Smedsrud, et al. 2021; Dumitru et al. 2023; Yue et al. 2024) | A privacy-preserving multi-hospital system optimized for these failures | Boundary-aware FL model with hard-case evaluation |
| FL does not protect updates after aggregation | FL, DP, HE, secure aggregation exist (Kaissis et al. 2021; Truhn et al. 2022; R. Xu et al. 2024; Hu and Li 2025) | A mechanism that makes past updates unreadable or unusable once aggregation ends | Time-decaying or self-destructing update keys |
| De-identification is separate from FL | DICOM and image de-identification are well studied (Kondylakis et al. 2024; Rempe et al. 2024; Rutherford et al. 2021; Shahid et al. 2022) | An integrated training pipeline that sanitizes metadata and pixel PHI before FL | Hospital-side de-identification stage in the same system |
| Deletion is mostly retrospective | Federated unlearning exists (G. Liu et al. 2021; Deng et al. 2024) | Immediate post-aggregation destruction rather than later retraining or correction | Automatic invalidation plus optional unlearning fallback |

### Five priority gaps

1.  **No end-to-end colorectal FL system combines segmentation, privacy hardening, and temporal destruction of updates.**

    Current polyp FL papers remain modular. They improve aggregation, communication efficiency, or generalization, but not the whole lifecycle of sensitive updates (Stelter et al. 2024; Fan et al. 2024; H. Pan et al. 2024; Chen et al. 2025; Zhang et al. 2025).

2.  **Post-breach safety is the clearest missing design target.**

    The literature is rich on privacy during training, but weak on what should happen to encrypted updates, gradients, or decryption material after the round closes (Pati et al. 2024; R. Xu et al. 2024; Hu and Li 2025). This is the most direct opening for the term self-destructing.

3.  **Secure aggregation is not the same as secure retention.**

    Secure aggregation protects intermediate visibility but does not itself guarantee that stored or later-accessed artifacts are harmless (Pasquini et al. 2021; Shi et al. 2024). A practical healthcare system needs both aggregation security and expiration semantics.

4.  **Colonoscopy FL still lacks strong integration with de-identification practice.**

    Metadata leakage, burned-in identifiers, and traceability of medical imaging remain real concerns (Kondylakis et al. 2024; Rempe et al. 2024; Rutherford et al. 2021). FL papers usually assume the training images are already safe, which is too weak for a deployment story.

5.  **The literature has not joined temporal cryptography with medical FL in colorectal imaging.**

    Timed-release and delay-based cryptography exist as a separate field (Medley et al. 2023; Yuan et al. 2024). Single-setup secure aggregation with forward and backward secrecy is now appearing in FL (Sultan et al. 2025). But colorectal multi-hospital FL with time-expiring update protection has not emerged in the reviewed literature.

## Patent-oriented novelty mapping

The strongest novelty claim is not that federated learning, differential privacy, homomorphic encryption, or segmentation are individually new. None of them are. The novelty lies in their combination around a new technical problem: **how to ensure that hospital model updates become unusable after aggregation, while preserving segmentation performance and compliance-oriented data handling in colorectal imaging**.

### Novelty checklist

| Component | Seen separately | Seen together in colorectal FL |
|:---|:---|:---|
| Polyp segmentation on Kvasir-SEG and related datasets | Yes (Jha, Ali, et al. 2021; Jha, Smedsrud, et al. 2021; Sanderson and Matuszewski 2022; Rajasekar et al. 2024; Ahamed et al. 2024) | No |
| Federated polyp segmentation | Yes (Stelter et al. 2024; Fan et al. 2024; H. Pan et al. 2024; Chen et al. 2025; Zhang et al. 2025) | No |
| DP, secure aggregation, or HE in medical FL | Yes (Kaissis et al. 2021; Truhn et al. 2022; R. Xu et al. 2024; Hu and Li 2025) | No |
| DICOM and image de-identification | Yes (Kondylakis et al. 2024; Rempe et al. 2024; Rutherford et al. 2021; Shahid et al. 2022) | No |
| Federated unlearning | Yes (G. Liu et al. 2021; Deng et al. 2024) | No |
| Timed or delay-based cryptography | Yes (Medley et al. 2023; Yuan et al. 2024; Sultan et al. 2025) | No |
| Temporal destruction of colorectal FL updates | Not found in the reviewed literature | No |

### Components that appear most defensible as a patent-oriented package

- Hospital-side sanitization of colonoscopy data before local training
- Local segmentation training with privacy-aware FL under non-IID conditions
- Encryption of model updates under per-round ephemeral or time-decaying keys
- Secure aggregation that only works within a valid round window
- Automatic invalidation or destruction of round keys and residual update artifacts after aggregation
- Optional audit or compliance layer that records round completion and destruction events without revealing patient data

This is best presented as a **technical system architecture** rather than as a medical diagnosis claim. The inventive point is the update lifecycle control in a federated medical imaging system.

## Recommended implementation roadmap

### Threat model

The system defends against a post-breach adversary who gains read access to a hospital server or the aggregation server after training has completed. This adversary can see stored ciphertexts, logs, cached gradients, and retained parameter artifacts but cannot interact with active key holders or rerun the aggregation protocol. Against a concurrent adversary during training, the system relies on secure aggregation and differential privacy (Kaissis et al. 2021; R. Xu et al. 2024; Pati et al. 2024). The temporal destruction mechanism specifically addresses the post-breach window, which existing FL systems leave open (Pasquini et al. 2021; Shi et al. 2024).

In plain terms, SDFL assumes breaches may happen. The design goal is that even if stored updates are accessed after the round has closed, the attacker should not be able to turn them into clinically meaningful patient information.

### Model choice

A practical base model is **ResUNet++ with a lightweight attention-enabled refinement layer**. ResUNet++ already has evidence on flat and sessile polyps and cross-dataset testing (Jha, Smedsrud, et al. 2021). Attention is reasonable here as an engineering choice rather than a novelty claim: transformer-convolution fusion improved full-resolution polyp segmentation in FCBFormer (Sanderson and Matuszewski 2022), and AdaptUNet used attention mechanisms to improve feature selection and contextual recovery in colorectal polyp segmentation (Rajasekar et al. 2024). Boundary-focused refinements are still justified by failure cases in DUCK-Net and BRNet (Dumitru et al. 2023; Yue et al. 2024).

The safest implementation path is therefore a **lightweight attention module on top of a proven segmentation backbone**, not a heavy redesign. A heavier transformer model such as FCBFormer may serve as an upper-bound comparator rather than the main deployment model (Sanderson and Matuszewski 2022).

### Federated training strategy

| Design choice | Recommendation | Rationale |
|:---|:---|:---|
| Base aggregation | FedProx | More stable than plain FedAvg under hospital heterogeneity (Arafath et al. 2025; A. Xu et al. 2022) |
| Domain robustness | Add frequency-based domain generalization | Domain shift is central in polyp FL (H. Pan et al. 2024; Q. Liu et al. 2021) |
| Personalization | Light local adapter or last-layer personalization | Helps centres with distinct scopes or acquisition styles (A. Xu et al. 2022; Hosseini et al. 2023) |
| Main benchmark data | Kvasir-SEG plus PolypGen or PolypDB style multi-centre splits | Single-dataset validation is too weak (Ali et al. 2021; Jha et al. 2024) |

### Privacy stack

| Layer | Recommendation | Why it matters |
|:---|:---|:---|
| Input protection | DICOM and pixel-text sanitization before training | FL does not solve metadata leakage (Kondylakis et al. 2024; Rempe et al. 2024; Shahid et al. 2022) |
| Statistical privacy | Client-side DP with reported privacy budget sweep | Needed against inversion and inference leakage (Adnan et al. 2021; Pati et al. 2024) |
| Cryptographic protection | Secure aggregation or selective HE-backed encrypted updates | Protects updates during aggregation while keeping computation practical (Truhn et al. 2022; R. Xu et al. 2024; Hu and Li 2025) |
| Temporal protection | Per-round ephemeral keys bound to an expiry timestamp $`T_r`$ | Makes updates usable only inside the round window rather than indefinitely |
| Retention control | Automatic deletion of cached ciphertexts, shares, and local plaintext updates once $`T_r`$ is reached | Turns self-destruction into a system property rather than a slogan |

A practical SDFL implementation does not need the heaviest possible cryptography in its first version. A realistic prototype can combine FedProx, DP-SGD, secure aggregation or selective HE, and round-specific key destruction while keeping segmentation performance clinically useful.

### Round lifecycle

| Stage | Action | Security meaning |
|:---|:---|:---|
| 1 | Sanitize input data at each hospital | Removes metadata and pixel-level identifiers before local training (Kondylakis et al. 2024; Rempe et al. 2024; Shahid et al. 2022) |
| 2 | Train local segmentation model | Keeps raw data inside the hospital boundary |
| 3 | Encrypt updates under a fresh per-round key and bind them to a coordinator-signed round certificate carrying expiry timestamp $`T_r`$ | Limits each round to its own cryptographic context and explicit validity window |
| 4 | Aggregate only inside the bounded window that ends at $`T_r`$, with the aggregator rejecting late or certificate-mismatched uploads | Prevents late reuse of stale updates and ties decryption to an active session |
| 5 | When $`T_r`$ is reached, destroy round keys, cached ciphertexts, and residual plaintext buffers | Leaves the global model intact while making per-round contributions cryptographically unrecoverable |

A simple way to present the round lifecycle is the following flow:

Sanitize local data → Receive coordinator-signed round certificate with $`T_r`$ → Train locally → Encrypt and tag update with the round certificate → Aggregate before $`T_r`$ → At $`T_r`$, reject late uploads and destroy keys and update artifacts → Retain only the global model

### Evaluation plan

The technical contribution should be tested on utility, privacy, and clinical reliability. The key experimental question is not only whether SDFL preserves segmentation quality, but whether leaked artifacts remain useful after the round has expired and whether the model can identify low-confidence cases that deserve closer review.

| Dimension | Recommended metrics |
|:---|:---|
| Segmentation utility | Dice, IoU, precision, recall, F2, HD95 or ASSD |
| Real-time suitability | FPS, latency, parameter count, communication cost |
| Generalization | Cross-centre and cross-dataset performance on PolypGen or PolypDB-style splits (Ali et al. 2021; Jha et al. 2024) |
| Privacy | epsilon and delta for DP, inversion attack quality, membership inference accuracy, success of post-expiry decryption attempts |
| Uncertainty quality | calibration error, failure-detection ability, uncertainty on hard or out-of-distribution cases (Lambert et al. 2022; Koutsoubis et al. 2024) |
| System overhead | encryption time, aggregation time, client memory, network payload, uncertainty inference overhead |

A sensible uncertainty layer should be kept narrow. The literature supports uncertainty estimation as a trust and quality-control tool in medical image segmentation (Lambert et al. 2022) and as a relevant reliability layer in federated medical imaging under heterogeneous data (Koutsoubis et al. 2024). It should therefore be used to flag unreliable segmentations or difficult cross-centre cases, not to redefine the core privacy contribution.

### Minimum baseline set

- Centralized training without privacy controls
- Plain FL with FedAvg
- FL with FedProx
- FL with DP only
- FL with secure aggregation or HE only
- SDFL with attention-enabled segmentation backbone but without uncertainty estimation
- Full SDFL stack with sanitization, DP, secure aggregation or HE, timestamp-bound self-destruction, and uncertainty estimation

## Working thesis for the project

The literature supports a clear working thesis: **the main unmet need is not another small gain on Kvasir-SEG, but a deployable colorectal federated learning system in which model updates are treated as temporary sensitive assets that are sanitized, protected, aggregated, and then invalidated at a round expiry timestamp**. Existing work supplies most of the individual building blocks (Kaissis et al. 2021; Truhn et al. 2022; R. Xu et al. 2024; Kondylakis et al. 2024; G. Liu et al. 2021), but the synthesis into one colorectal, multi-hospital, temporally protected system has not yet been established in the reviewed literature.

A concise research positioning statement is therefore: **Self-Destructing Federated Learning introduces timestamp-bound temporal privacy into healthcare federated learning so that encrypted model updates and related key material become unusable once the aggregation round expires, reducing post-breach leakage risk in collaborative colorectal diagnosis systems.**

## Inventive core

The inventive core of SDFL is a three-element mechanism:

1.  each FL round defines an expiry timestamp $`T_r`$ in a coordinator-signed round certificate and generates a fresh cryptographic context used only for that round’s update encryption
2.  the aggregation server accepts and processes updates only until $`T_r`$, verifying certificate validity and rejecting late, replayed, or context-mismatched round artifacts
3.  when $`T_r`$ is reached, the server and participating clients destroy the round’s decryption material, cached update ciphertexts, and residual plaintext gradient buffers, leaving the aggregated global model but making per-round contributions cryptographically unrecoverable

Differential privacy, selective homomorphic encryption, DICOM sanitization, attention-based segmentation, and uncertainty estimation are all useful embodiments of this system, not mandatory claim elements. The novelty claim does not depend on all of them simultaneously.

This is the point that distinguishes SDFL from ordinary FL hardening. Traditional privacy-preserving FL mainly aims to stop unauthorized access. SDFL aims to reduce the value of information even if access occurs later.

### Narrow claim summary

| Element | Core claim role |
|:---|:---|
| Round-specific update protection | Fresh cryptographic context and coordinator-signed expiry timestamp $`T_r`$ for each aggregation round |
| Bounded aggregation window | Enforces temporal validity and rejects late update reuse |
| Automatic invalidation after closure | Removes post-breach recoverability of local contributions |

---

## References

Adnan, Mohammed, S. Kalra, Jesse C. Cresswell, Graham W. Taylor, and H. Tizhoosh. 2021. “Federated Learning and Differential Privacy for Medical Image Analysis.” *Scientific Reports* 12 (November). <https://doi.org/10.1038/s41598-022-05539-7>.

Ahamed, M., Md. Rabiul Islam, Md. Nahiduzzaman, Md. Jawadul Karim, M. Ayari, and A. Khandakar. 2024. “Automated Detection of Colorectal Polyp Utilizing Deep Learning Methods With Explainable AI.” *IEEE Access* 12: 78074–100. <https://doi.org/10.1109/ACCESS.2024.3402818>.

Ali, Sharib, Debesh Jha, N. Ghatwary, et al. 2021. “A Multi-Centre Polyp Detection and Segmentation Dataset for Generalisability Assessment.” *Scientific Data* 10 (June). <https://doi.org/10.1038/s41597-023-01981-y>.

Arafath, Md., Abhijit Kumar Ghosh, Md Rony Ahmed, et al. 2025. “Colorectal Cancer Histopathological Grading Using Multi-Scale Federated Learning.” *ArXiv* abs/2511.03693 (November). <https://doi.org/10.48550/arXiv.2511.03693>.

Ball, Marshall, James Bell-Clark, Adria Gascon, P. Kairouz, Sewoong Oh, and Zhiye Xie. 2024. “Secure Stateful Aggregation: A Practical Protocol with Applications in Differentially-Private Federated Learning.” *ArXiv* abs/2410.11368 (October). <https://doi.org/10.48550/arXiv.2410.11368>.

Bhattacharya, Debayan, D. Eggert, C. Betz, and A. Schlaefer. 2022. “Squeeze and Multi‐context Attention for Polyp Segmentation.” *International Journal of Imaging Systems and Technology* 33 (August): 123–42. <https://doi.org/10.1002/ima.22795>.

Chen, Xingchi, Fa Zhu, Dazhou Li, et al. 2025. “Towards Clinically Applicable Large-Model-Based Privacy-Preserving Polyp Segmentation: A Federated LoRA Approach to Colonoscopy.” *IEEE Journal of Biomedical and Health Informatics* PP (December). <https://doi.org/10.1109/JBHI.2025.3639279>.

Deng, Zhi-Hui, Luyang Luo, and Hao Chen. 2024. “Enable the Right to Be Forgotten with Federated Client Unlearning in Medical Imaging.” *ArXiv* abs/2407.02356 (July). <https://doi.org/10.48550/arXiv.2407.02356>.

Dumitru, Razvan-Gabriel, Darius Peteleaza, and Catalin Craciun. 2023. “Using DUCK-Net for Polyp Image Segmentation.” *Scientific Reports* 13 (June). <https://doi.org/10.1038/s41598-023-36940-5>.

Fan, Kefeng, Cun Xu, Xuguang Cao, Kaijie Jiao, and Wei Mo. 2024. “Tri-Branch Feature Pyramid Network Based on Federated Particle Swarm Optimization for Polyp Segmentation.” *Mathematical Biosciences and Engineering : MBE* 21 1 (January): 1610–24. <https://doi.org/10.3934/mbe.2024070>.

Ghosh, Durjoy, Maliha Mehjabin, Md Eshmam Rayed, M. F. Mridha, and M. Kabir. 2026. “Advancements and Challenges of Federated Learning in Medical Imaging: A Systematic Literature Review.” *Artificial Intelligence Review* 59 (January). <https://doi.org/10.1007/s10462-025-11489-z>.

Halimi, Anisa, S. Kadhe, Ambrish Rawat, and Nathalie Baracaldo. 2022. “Federated Unlearning: How to Efficiently Erase a Client in FL?” *ArXiv* abs/2207.05521 (July). <https://doi.org/10.48550/arXiv.2207.05521>.

Hatamizadeh, Ali, Hongxu Yin, Pavlo Molchanov, et al. 2022. “Do Gradient Inversion Attacks Make Federated Learning Unsafe?” *IEEE Transactions on Medical Imaging* 42 (February): 2044–56. <https://doi.org/10.1109/TMI.2023.3239391>.

Hosseini, Seyedeh Maryam, Milad Sikaroudi, Morteza Babaie, and H. Tizhoosh. 2023. “Proportionally Fair Hospital Collaborations in Federated Learning of Histopathology Images.” *IEEE Transactions on Medical Imaging* 42 (January): 1982–95. <https://doi.org/10.1109/TMI.2023.3234450>.

Hu, Chenghao, and Baochun Li. 2025. “MaskCrypt: Federated Learning With Selective Homomorphic Encryption.” *IEEE Transactions on Dependable and Secure Computing* 22 (January): 221–33. <https://doi.org/10.1109/TDSC.2024.3392424>.

Jha, Debesh, Sharib Ali, Nikhil Kumar Tomar, et al. 2021. “Real-Time Polyp Detection, Localization and Segmentation in Colonoscopy Using Deep Learning.” *Ieee Access* 9 (March): 40496–510. <https://doi.org/10.1109/ACCESS.2021.3063716>.

Jha, Debesh, P. Smedsrud, Dag Johansen, et al. 2021. “A Comprehensive Study on Colorectal Polyp Segmentation With ResUNet++, Conditional Random Field and Test-Time Augmentation.” *IEEE Journal of Biomedical and Health Informatics* 25 (January): 2029–40. <https://doi.org/10.1109/JBHI.2021.3049304>.

Jha, Debesh, Nikhil Kumar Tomar, Vanshali Sharma, et al. 2024. “PolypDB: A Curated Multi-Center Dataset for Development of AI Algorithms in Colonoscopy.” *ArXiv* abs/2409.00045 (August). <https://doi.org/10.48550/arXiv.2409.00045>.

Kaissis, Georgios, A. Ziller, Jonathan Passerat-Palmbach, et al. 2021. “End-to-End Privacy Preserving Deep Learning on Multi-Institutional Medical Imaging.” *Nature Machine Intelligence* 3 (May): 473–84. <https://doi.org/10.1038/s42256-021-00337-8>.

Kondylakis, H., R. Catalán, Sara Martinez Alabart, et al. 2024. “Documenting the de-Identification Process of Clinical and Imaging Data for AI for Health Imaging Projects.” *Insights into Imaging* 15 (May). <https://doi.org/10.1186/s13244-024-01711-x>.

Koutsoubis, Nikolas, Yasin Yilmaz, Ravichandran Ramachandran, M. Schabath, and Ghulam Rasool. 2024. “Privacy Preserving Federated Learning in Medical Imaging with Uncertainty Estimation.” *ArXiv* abs/2406.12815 (June). <https://doi.org/10.48550/arXiv.2406.12815>.

Lambert, Benjamin, Florence Forbes, A. Tucholka, Senan Doyle, Harmonie Dehaene, and M. Dojat. 2022. “Trustworthy Clinical AI Solutions: A Unified Review of Uncertainty Quantification in Deep Learning Models for Medical Image Analysis.” *Artificial Intelligence in Medicine* 150 (October): 102830. <https://doi.org/10.48550/arXiv.2210.03736>.

Liu, Gaoyang, Xiaoqian Ma, Yang Yang, Chen Wang, and Jiangchuan Liu. 2021. “FedEraser: Enabling Efficient Client-Level Data Removal from Federated Learning Models.” *2021 IEEE/ACM 29th International Symposium on Quality of Service (IWQOS)*, June 25, 1–10. <https://doi.org/10.1109/IWQOS52092.2021.9521274>.

Liu, Quande, Cheng Chen, J. Qin, Q. Dou, and P. Heng. 2021. “FedDG: Federated Domain Generalization on Medical Image Segmentation via Episodic Learning in Continuous Frequency Space.” *2021 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, March 10, 1013–23. <https://doi.org/10.1109/CVPR46437.2021.00107>.

Liu, Yang, Zhuo Ma, Ximeng Liu, Zhuzhu Wang, Siqi Ma, and Ke Ren. 2019. “Revocable Federated Learning: A Benchmark of Federated Forest.” *ArXiv* abs/1911.03242 (November).

Liu, Yi, Lei Xu, Xingliang Yuan, Cong Wang, and Bo Li. 2022. “The Right to Be Forgotten in Federated Learning: An Efficient Realization with Rapid Retraining.” *IEEE INFOCOM 2022 - IEEE Conference on Computer Communications*, March 14, 1749–58. <https://doi.org/10.1109/INFOCOM48880.2022.9796721>.

Ma, Jing, Si-Ahmed Naas, S. Sigg, and X. Lyu. 2021. “Privacy‐preserving Federated Learning Based on Multi‐key Homomorphic Encryption.” *International Journal of Intelligent Systems* 37 (April): 5880–901. <https://doi.org/10.1002/int.22818>.

Ma, Zhuo, Jianfeng Ma, Yinbin Miao, Yingjiu Li, and R. Deng. 2022. “ShieldFL: Mitigating Model Poisoning Attacks in Privacy-Preserving Federated Learning.” *IEEE Transactions on Information Forensics and Security* 17: 1639–54. <https://doi.org/10.1109/tifs.2022.3169918>.

Medley, Liam, Angelique Faye Loe, and E. Quaglia. 2023. “SoK: Delay-Based Cryptography.” *2023 IEEE 36th Computer Security Foundations Symposium (CSF)*, July 1, 169–83. <https://doi.org/10.1109/CSF57540.2023.00028>.

Pan, Hongyi, Debesh Jha, Koushik Biswas, and Ulas Bagci. 2024. “Frequency-Based Federated Domain Generalization for Polyp Segmentation.” *ICASSP 2025 - 2025 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*, October 2, 1–5. <https://doi.org/10.1109/ICASSP49660.2025.10889662>.

Pan, Liangrui, Mao-Feng Huang, Lian-min Wang, Pinle Qin, and Shaoliang Peng. 2024. “FedDP: Privacy-Preserving Method Based on Federated Learning for Histopathology Image Segmentation.” *2024 IEEE International Conference on Bioinformatics and Biomedicine (BIBM)*, November 7, 2325–31. <https://doi.org/10.1109/BIBM62325.2024.10822021>.

Pasquini, Dario, Danilo Francati, and G. Ateniese. 2021. “Eluding Secure Aggregation in Federated Learning via Model Inconsistency.” *Proceedings of the 2022 ACM SIGSAC Conference on Computer and Communications Security*, ahead of print, November 14. <https://doi.org/10.1145/3548606.3560557>.

Pati, Sarthak, Sourav Kumar, Amokh Varma, et al. 2024. “Privacy Preservation for Federated Learning in Health Care.” *Patterns* 5 (July). <https://doi.org/10.1016/j.patter.2024.100974>.

Rajasekar, Devika, Girish Theja, M. Prusty, and S. Chinara. 2024. “Efficient Colorectal Polyp Segmentation Using Wavelet Transformation and AdaptUNet: A Hybrid U-Net.” *Heliyon* 10 (June). <https://doi.org/10.1016/j.heliyon.2024.e33655>.

Rempe, M., Lukas Heine, Constantin Seibold, Fabian Hörst, and J. Kleesiek. 2024. “De-Identification of Medical Imaging Data: A Comprehensive Tool for Ensuring Patient Privacy.” *European Radiology* 35 (October): 7809–18. <https://doi.org/10.1007/s00330-025-11695-x>.

Rutherford, Michael W., S. Mun, B. Levine, et al. 2021. “A DICOM Dataset for Evaluation of Medical Image de-Identification.” *Scientific Data* 8 (July). <https://doi.org/10.1038/s41597-021-00967-y>.

Sanderson, Edward, and B. Matuszewski. 2022. “FCN-Transformer Feature Fusion for Polyp Segmentation.” *Annual Conference on Medical Image Understanding and Analysis*, August 17, 892–907. <https://doi.org/10.1007/978-3-031-12053-4_65>.

Shahid, Arsalan, Mehran H. Bazargani, Paul Banahan, et al. 2022. “A Two-Stage De-Identification Process for Privacy-Preserving Medical Image Analysis.” *Healthcare* 10 (April). <https://doi.org/10.3390/healthcare10050755>.

Shi, Shanghao, Md Shahedul Haque, Abhijeet Parida, et al. 2024. *MedLeak: Multimodal Medical Data Leakage in Secure Federated Learning with Crafted Models*. In *2025 IEEE/ACM Conference on Connected Health: Applications, Systems and Engineering Technologies (CHASE)*. <https://doi.org/10.1145/3721201.3721375>.

Skorupko, Grzegorz, Fotios Avgoustidis, Carlos Mart’in-Isla, et al. 2025. “Federated nnU-Net for Privacy-Preserving Medical Image Segmentation.” *Scientific Reports* 15 (March). <https://doi.org/10.1038/s41598-025-22239-0>.

Stelter, Lena, V. Corbetta, Regina Beets-Tan, and Wilson Silva. 2024. “Assessing the Impact of Federated Learning and Differential Privacy on Multi-Centre Polyp Segmentation.” *2024 46th Annual International Conference of the IEEE Engineering in Medicine and Biology Society (EMBC)*, July 1, 1–4. <https://doi.org/10.1109/EMBC53108.2024.10782682>.

Sultan, N., Yanan Bo, Yansong Gao, et al. 2025. “Setup Once, Secure Always: A Single-Setup Secure Federated Learning Aggregation Protocol with Forward and Backward Secrecy for Dynamic Users.” Preprint, February 13.

Truhn, D., S. Tayebi Arasteh, O. Lester Saldanha, et al. 2022. “Encrypted Federated Learning for Secure Decentralized Collaboration in Cancer Image Analysis.” *Medical Image Analysis* 92 (July). <https://doi.org/10.1016/j.media.2023.103059>.

Wei, Kaimin, Jin Qian, Chengkun Jia, et al. 2025. “Medical Image Privacy in Federated Learning: Segmentation-Reorganization and Sparsified Gradient Matching Attacks.” *IEEE Journal of Biomedical and Health Informatics* 30 (September): 1443–51. <https://doi.org/10.1109/JBHI.2025.3593631>.

Xu, An, Wenqi Li, Pengfei Guo, et al. 2022. “Closing the Generalization Gap of Cross-Silo Federated Medical Image Segmentation.” *2022 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, March 18, 20834–43. <https://doi.org/10.1109/CVPR52688.2022.02020>.

Xu, Runhua, Bo Li, Chao Li, J. Joshi, Shuai Ma, and Jianxin Li. 2024. “TAPFed: Threshold Secure Aggregation for Privacy-Preserving Federated Learning.” *IEEE Transactions on Dependable and Secure Computing* 21 (September): 4309–23. <https://doi.org/10.1109/TDSC.2024.3350206>.

Yuan, Ke, Ziwei Cheng, Keyan Chen, et al. 2024. “Multiple Time Servers Timed-Release Encryption Based on Shamir Secret Sharing for EHR Cloud System.” *Journal of Cloud Computing* 13 (June). <https://doi.org/10.1186/s13677-024-00676-y>.

Yue, Guanghui, Yuanyan Li, Wenchao Jiang, Wei Zhou, and Tianwei Zhou. 2024. “Boundary Refinement Network for Colorectal Polyp Segmentation in Colonoscopy Images.” *IEEE Signal Processing Letters* 31: 954–58. <https://doi.org/10.1109/LSP.2024.3378106>.

Zhang, Mengru, Tianyu Huang, Weibin Chen, Xiaochuan Sun, and Xuelei Xi. 2025. “FedDW: An Adaptive Weight Aggregation Federated Learning Framework for Multi-Institutional Collaborative Polyp Segmentation.” *Engineering Research Express* 8 (December). <https://doi.org/10.1088/2631-8695/ae3272>.
