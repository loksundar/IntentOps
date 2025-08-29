# ACCEPTANCE.md — Intent OPS

**Version:** 1.0  
**Scope:** Intent classification + NER + (optional) OOS detection, with production ops on AWS (SageMaker).  
**Applies To:** Staging → Production promotion.

---

## 1) Product Metrics (Model Quality)

### Datasets & Splits
- **Intent:** BANKING77  
- **NER:** WNUT-2017  
- **OOS (optional):** small CLINC OOS slice  
- **Reproducibility:** Fixed seed = `42`. Deterministic preprocessing (see `config.yaml`).  
- **Eval split:** Use held-out test split produced by `make_splits.py` (no leakage; verified by test).

### Targets (must meet or exceed)
| Task | Dataset | Metric | Target |
|---|---|---:|---:|
| Intent | BANKING77 | Top-1 Accuracy | **≥ 92.0%** |
| NER | WNUT-2017 | Micro-F1 (token-level) | **≥ 45.0%** |
| OOS (optional) | CLINC OOS slice | AUROC | **≥ 0.85** |

**Measurement Protocol**
- Intent: compute accuracy on test split; include confusion matrix (CSV/PNG).  
- NER: compute **micro-F1** over BIO tags on test split; include per-entity report.  
- OOS: compute AUROC using softmax-threshold or entropy heuristic; include the chosen threshold and ROC curve.

**Artifacts Required (commit under `artifacts/eval/`):**
- `intent_metrics.json` (accuracy, confusion matrix path)  
- `ner_metrics.json` (micro-F1, per-entity)  
- `oos_metrics.json` (AUROC, threshold) [if applicable]  
- `model_card.md` links to the above

---

## 2) Ops SLOs (Service Level Objectives)

**Under staging load, per model variant:**
- **Latency:** p95 ≤ **150 ms** at **2 rps/instance** (container warm, after first token).  
- **Error rate:** < **0.5%** HTTP 5xx over 10 min window.  
- **Rollback:** Blue/green rollback proves successful when any alarm breaches.

**Measurement Protocol**
- Run a controlled load (e.g., 2 rps for 10 minutes) against the **staging endpoint**.  
- Capture CloudWatch metrics: `ModelLatency`/`Invocation4XXErrors`/`Invocation5XXErrors`.  
- Store a screenshot or exported JSON of the dashboard in `monitoring/screens/`.

**Artifacts Required:**
- `monitoring/screens/p95_latency.png`  
- `monitoring/screens/error_rate.png`  
- `ops/rollback_evidence.md` (timestamped log/screens showing automatic rollback executed)

---

## 3) Governance

- **Model Card:** Completed and checked in at `governance/model_card.md` (intended use, datasets & licenses, metrics, risks, eval plots).
- **Manual Approval:** Required before any **production** deploy. Approval recorded via PR comment or `pipelines/approve_deploy.py` output.
- **Licenses:** `DATA_LICENSES.md` filled with sources and license notes for BANKING77, WNUT-2017, CLINC OOS slice.
- **Change Control:** Any change to this document requires a PR and explicit re-approval from both signers below.

---

## 4) Safety Gates & Evidence

Promotion from **train → registry → staging → prod** is blocked unless:
1) **Metrics Gate:** Step 5 pipeline’s **Condition** sees model meets Section 1 targets.
2) **Ops Gate:** Staging endpoint meets Section 2 SLOs under smoke load.
3) **Governance Gate:** Model Card present + manual approval recorded.

**Where Evidence Lives (must exist in the PR):**
- `artifacts/eval/*.json|png`  
- `monitoring/screens/*.png`  
- `governance/model_card.md`  
- `ops/rollback_evidence.md`

---

## 5) Non-Goals / Clarifications

- Quality targets are on **test** split only; do not tune on test.  
- Throughput beyond 2 rps/instance is out of scope for acceptance (can be optimized later).  
- OOS is optional; if included, it must meet AUROC ≥ 0.85.

---

## 6) Approval & Sign-off (required)

By signing, you confirm all artifacts exist and gates are satisfied.

- **Owner (Engineering):** _Name_ — _Signature_ — _Date_  
- **Approver (Ops/Governance):** _Name_ — _Signature_ — _Date_

**Current Status:** ☐ Pending  ☐ Approved  ☐ Rejected  
**Link to Evidence PR:** _URL_

