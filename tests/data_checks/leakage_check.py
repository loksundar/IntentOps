# tests/data_checks/leakage_check.py
import json
from pathlib import Path

def load_csv_texts(path: Path):
    import pandas as pd
    df = pd.read_csv(path)
    return set(df["text_norm"].astype(str).tolist())

def load_jsonl_sentences(path: Path):
    s = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            s.add(" ".join(ex["tokens"]))
    return s

def check_disjoint(name, a, b, c):
    inter_ab = a & b
    inter_ac = a & c
    inter_bc = b & c
    ok = (len(inter_ab)==0 and len(inter_ac)==0 and len(inter_bc)==0)
    return ok, {"ab": len(inter_ab), "ac": len(inter_ac), "bc": len(inter_bc)}

def banking77():
    base = Path("data/processed/banking77")
    tr = load_csv_texts(base / "train.csv")
    va = load_csv_texts(base / "val.csv")
    te = load_csv_texts(base / "test.csv")
    ok, overlaps = check_disjoint("banking77", tr, va, te)
    return ok, overlaps

def wnut2017():
    base = Path("data/processed/wnut2017")
    tr = load_jsonl_sentences(base / "train.jsonl")
    va = load_jsonl_sentences(base / "val.jsonl")
    te = load_jsonl_sentences(base / "test.jsonl")
    ok, overlaps = check_disjoint("wnut2017", tr, va, te)
    return ok, overlaps

if __name__ == "__main__":
    b_ok, b_ov = banking77()
    n_ok, n_ov = wnut2017()
    print("BANKING77 leakage:", "PASS" if b_ok else "FAIL", b_ov)
    print("WNUT2017 leakage:", "PASS" if n_ok else "FAIL", n_ov)
    if b_ok and n_ok:
        print("\nSAFETY GATE (Step 3): PASS")
    else:
        print("\nSAFETY GATE (Step 3): FAIL — fix splits before proceeding.")
