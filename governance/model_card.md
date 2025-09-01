# Model Card — Intent OPS v1

## 1. Model Overview
- **Model name:** intent-ops-nlu-v1
- **Tasks:** Intent classification (BANKING77), Named Entity Recognition (WNUT-2017), optional OOS detection.
- **Owner:** Team NLU (@ml-lead, @product-owner)
- **Version:** 1.0.0
- **Registry entry:** sagemaker://model-registry/intent-ops/versions/TBD
- **Repo commit:** `<git_sha>`
- **Docker image digest:** `<sha256:...>`

## 2. Intended Use
- **Intended users:** Backend services powering chatbots/assist flows for banking-style intents; internal ops dashboards consuming entities.
- **Intended context:** English, short user utterances (3–30 tokens).
- **Out-of-scope:** Medical/legal advice, multilingual, long-form documents, PII extraction for compliance workflows.

## 3. Datasets & Licenses
- **BANKING77** (intent). Source: Hugging Face. License: per upstream.  
- **WNUT-2017** (NER). Source: official. License: per upstream.  
- **OOS slice** (optional). Source: derived; see `DATA_LICENSES.md` for details.
- **Preprocessing:** Deterministic tokenizer settings, lowercase policy documented in `config.yaml`.
- **Data hashes:** See `artifacts/eval/eval.json`.

## 4. Training & Inference
- **Architecture:** Lightweight transformer head for intent; BiLSTM-CRF or light transformer head for NER; OOS via calibrated thresholds.
- **Hardware:** `ml.g5.xlarge` (train), `ml.c6i.large` or `ml.g5.xlarge` (inference, if GPU used).
- **Hyperparameters:** See `artifacts/train/config.json`.
- **Throughput & Latency:** p95 ≤ 150 ms @ 2 rps/instance (see SLOs).

## 5. Evaluation
- **Intent (BANKING77, test):** Top-1 = `TBD` (target ≥ 92.0%)
- **NER (WNUT-2017, test):** Micro-F1 = `TBD` (target ≥ 45.0%)
- **OOS (optional):** AUROC = `TBD` (target ≥ 0.85)
- **Artifacts:** Confusion matrix (intent), per-label F1 (NER), ROC curves (OOS) embedded below or linked.
- **Reproducibility:** RANDOM_SEED=2025; dataset hashes recorded.

## 6. Risks & Mitigations
- **Ambiguity/OOS:** Misclassification on unseen intents → OOS thresholding, fallback dialog flows.
- **Entity boundary errors:** Frequent on social/noisy text → confidence-aware highlighting, conservative use of entities for automation.
- **Bias/Fairness:** Domain terms may reflect banking-specific jargon → monitor per-intent performance; collect feedback loop labels.

## 7. Data Retention & Privacy
- **Retention:** Request/response capture in staging for monitoring; masked fields if applicable. Retention period: `TBD` days.
- **PII:** No training PII expected; ingestion PII scan must report near-zero and be remediated.

## 8. Security & Compliance
- **IAM:** Least-privilege roles; bucket prefix policies.
- **Networking:** VPC endpoints for SageMaker/S3 recommended.
- **Compliance:** This model does not make legal/medical claims.

## 9. Failure Modes & Runbooks
- **High latency:** Scale-out or rollback; see `RUNBOOK.md#latency`.
- **Error spikes:** Auto-rollback triggers; check alarms and logs.
- **Drift detected:** Triage with drift dashboard; initiate retrain toggle.

## 10. Versioning & Approvals
- **Semantic versioning:** MAJOR.MINOR.PATCH tied to registry versions.
- **Approvals required:** ML Lead + Product/Owner.
- **Approval record:** attached as PR comments and registry notes.

## 11. Contacts
- **On-call:** `#nlu-oncall` (Slack) / PagerDuty: `NLU-Primary`
- **Owner email:** `nlu-owner@example.com`

*Last updated:* `<YYYY-MM-DD>`
