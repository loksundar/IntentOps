# ACCEPTANCE.md

## Project: Intent OPS (MLOps, not GenAI)

### Purpose
Define what “done & production-ready” means for the Intent OPS service covering quality, reliability, rollout safety, governance, and cost/safety posture. This file is the single source of truth for release gating.

---

## 1) Product & ML Quality Criteria

### 1.1 Datasets & Splits (frozen for v1)
- **Intent:** BANKING77 (HF canonical split or fixed-seed 80/10/10 if regenerated), English.
- **NER:** WNUT-2017 (official train/dev/test). BIO tagging; “O” excluded from F1.
- **OOS (optional):** small CLINC-style OOS slice (~1–5k examples) with 20–40% OOS rate, held-out; used only for AUROC.
- **Reproducibility:** `RANDOM_SEED=2025`; all preprocessing deterministically versioned under `data/processed/` with immutable artifact hashes recorded in evaluation JSON.

### 1.2 Target Metrics (must meet or exceed)
- **Intent Accuracy (BANKING77, test):** **Top-1 ≥ 92.0%**  
  - *Definition:* `correct / total` after argmax on softmax (or calibrated scores).
  - *Aggregation:* macro not needed; dataset balanced.
- **NER Quality (WNUT-2017, test):** **Micro-F1 ≥ 45.0%**  
  - *Definition:* token-level micro-F1 across entity tags; BIO scheme; ignore “O”.
- **OOS Detection (optional set):** **AUROC ≥ 0.85**  
  - *Definition:* AUROC over OOS vs in-domain using calibrated score/entropy/energy threshold.
- **Overfitting Check:** Train–Val gap thresholds documented in the baseline notebook; flag if exceeded by >3 pts accuracy (intent) or >5 pts F1 (NER).
- **Sanity Test:** Randomized-label training must fail (≈ chance performance).

### 1.3 Evaluation Protocol (how we measure)
- **Exact scripts:** `src/eval/intent_eval.py`, `src/eval/ner_eval.py`, `src/eval/oos_eval.py`.
- **Outputs:** `artifacts/eval/eval.json` containing: metrics, confusion matrix (intent), per-label F1 (NER), ROC (OOS), dataset hashes, code commit, Docker image digest, and wall-clock & throughput during eval.

---

## 2) Operational SLOs & Rollout Safety

### 2.1 SLOs (per instance, staging & prod, steady state)
- **Latency:** **p95 ≤ 150 ms** at **2 RPS/instance** measured **end-to-end** (API Gateway → model → response), excluding client network.  
  - *Load profile:* warm instances, 1-minute ramp, 10-minute steady.
- **Error Rate:** **< 0.5%** server-side (**5xx + timeouts**). 4xx are tracked but do not count toward SLO.
- **Availability:** Target ≥ 99.9% monthly (informational for v1).

**Measurement tooling:** Prefer **k6** (CLI, in CI) or **Locust**. Scripts live in `tests/load/`. Results must be uploaded as artifacts and summarized in `eval.json`.

### 2.2 Blue/Green, Canary, and Rollback (must-prove)
- **Staging:** Blue = current, Green = candidate. Begin with **100% Blue**.
- **Canary to Prod:** Route **10% to Green** for ≥15 minutes.
- **Alarms (CloudWatch):**  
  - `p95_latency_ms > 150` for 5 consecutive minutes  
  - `server_error_rate > 0.5%` for 5 consecutive minutes  
  - (optional) **Accuracy proxy**: class-distribution drift or shadow eval delta beyond thresholds.
- **Auto-Rollback:** Alarm triggers **Lambda** that returns routing to **100% Blue** within **≤ 2 minutes**. Evidence (logs + screenshots) required once per release train.

---

## 3) Governance & Compliance

### 3.1 Model Card (mandatory before prod)
- **Location:** `governance/model_card.md` per approved template.
- **Contents:** intended use, datasets & licenses, metrics (with CIs), known risks & mitigations (OOS/ambiguity, entity boundary errors), fairness notes, data retention, security posture, and failure modes with operator runbook links.
- **Artifacts:** link to `eval.json`, confusion matrices, ROC plots, drift baselines.

### 3.2 Approvals & Promotion
- **Registry:** SageMaker Model Registry entry set to **Pending manual approval**.
- **Approver Roles:** at least 1 **ML Lead** + 1 **Product/Owner** approval required.  
- **Enforcement:** CI/CD policy blocks deploys unless the approved package version tag is present (`approved: true`).

### 3.3 Data & Licenses
- **DATA_LICENSES.md** lists BANKING77, WNUT-2017, and OOS set with source and license text/links.
- **PII:** Pre-ingestion regex pass (emails, phones) must report **near-zero**; any findings documented and scrubbed prior to training.

---

## 4) Security, Observability & Cost (v1 bar)

- **IAM:** least-privilege roles for SageMaker, CodeBuild/CodePipeline; bucket access restricted by prefix.
- **Networking:** (Recommended) VPC endpoints for S3/SageMaker; public disabled where feasible.
- **Data Capture:** Request/response capture enabled in **staging** (masked if needed), used for drift & OOS monitoring.
- **Metrics & Dashboards:** CloudWatch dashboard must show invocations, p50/p95 latency, error%, InvocationsPerInstance, drift score, OOS rate.
- **Cost:** Document instance family & autoscaling policy; teardown script `scripts/cleanup.py`. Idle endpoints must be stopped in non-prod.

---

## 5) Deliverables Checklist (what must exist at release)

- `ACCEPTANCE.md` (this file) committed.
- `governance/model_card.md` with links to artifacts.
- `artifacts/eval/eval.json` from the **exact** candidate build.
- CloudWatch dashboard JSON (`monitoring/dashboards/prod.json`) and screenshot embedded in README.
- Evidence of **successful auto-rollback** (log excerpt + screenshot).
- Demo script `DEMO.md`: canary → alarm → rollback, plus example predictions incl. OOS & NER.

---

## 6) Non-Goals (v1)
- Multilingual support, on-prem deployment, and advanced active-learning UX are out of scope for v1.
- Human-in-the-loop UI beyond thumbs-up/down API.

---

## 7) Change Control
Any edits to **targets** or **protocols** require a PR that updates this file and the evaluation scripts, with sign-offs from ML Lead and Product/Owner.

---

## 8) Sign-off

- **ML Lead:** __________________  **Date:** __________  
- **Product/Owner:** _____________  **Date:** __________

