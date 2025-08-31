# tests/baselines/baseline_gates.py
import json
from pathlib import Path

INTENT = Path("artifacts/baselines/intent/metrics.json")
INTENT_SANITY = Path("artifacts/baselines/intent/sanity.json")
NER = Path("artifacts/baselines/ner/metrics.json")
OOS = Path("artifacts/baselines/intent/oos.json")  # optional

# thresholds (tunable)
INTENT_MAX_GAP = 0.08   # 8 pp train - val
NER_MAX_GAP    = 0.12   # 12 pp train - val
RAND_MAX_ACC   = 0.10   # sanity: random labels must be <=10% on val

def main():
    ok = True
    if INTENT.exists():
        m = json.loads(INTENT.read_text())
        gap = m["train_acc"] - m["val_acc"]
        print(f"Intent acc train={m['train_acc']:.4f} val={m['val_acc']:.4f} gap={gap:.4f}")
        if gap > INTENT_MAX_GAP:
            print("FAIL: Intent overfitting gap too high.")
            ok = False
    else:
        print("WARN: Intent metrics missing."); ok = False

    if INTENT_SANITY.exists():
        s = json.loads(INTENT_SANITY.read_text())
        if s["val_acc_random_labels"] > RAND_MAX_ACC:
            print(f"FAIL: Random-label sanity too high ({s['val_acc_random_labels']:.3f}).")
            ok = False
    else:
        print("WARN: Intent sanity missing."); ok = False

    if NER.exists():
        n = json.loads(NER.read_text())
        gap = n["train_micro_f1"] - n["val_micro_f1"]
        print(f"NER micro-F1 train={n['train_micro_f1']:.4f} val={n['val_micro_f1']:.4f} gap={gap:.4f}")
        if gap > NER_MAX_GAP:
            print("FAIL: NER overfitting gap too high.")
            ok = False
        # record if meets Step 0 target
        if n["test_micro_f1"] < 0.45:
            print("NOTE: NER test micro-F1 below 0.45 acceptance target (okay for baseline; pipeline gate will enforce).")
    else:
        print("WARN: NER metrics missing."); ok = False

    if OOS.exists():
        o = json.loads(OOS.read_text())
        print(f"OOS AUROC (optional): {o['auroc']:.4f}  (n_ind={o['n_ind']}, n_oos={o['n_oos']})")
    else:
        print("NOTE: OOS AUROC skipped.")

    print("\nSAFETY GATE (Step 4):", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
