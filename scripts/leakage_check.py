# scripts/leakage_check.py
# Usage: python scripts/leakage_check.py
import sys, json
from pathlib import Path
import pandas as pd
import pyarrow as pa, pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]

def set_from_csv_text(p: Path, col="text"):
    df = pd.read_csv(p)
    return set(df[col].astype(str).tolist())

def set_from_parquet_tokens(p: Path):
    table = pq.read_table(p)
    df = table.to_pandas()
    # Join tokens to a single string to compare exact sequences
    return set(" ".join(toks) for toks in df["tokens"].tolist())

def check_overlap(name, a_set, b_set):
    inter = a_set.intersection(b_set)
    return name, len(inter), list(inter)[:5]

def main():
    issues = []

    # BANKING77: text overlaps across train/val/test
    b77_dir = ROOT / "data" / "processed" / "banking77"
    train_s = set_from_csv_text(b77_dir / "train.csv", "text")
    val_s   = set_from_csv_text(b77_dir / "val.csv", "text")
    test_s  = set_from_csv_text(b77_dir / "test.csv", "text")

    for name, n, sample in [
        check_overlap("b77_train_vs_val", train_s, val_s),
        check_overlap("b77_train_vs_test", train_s, test_s),
        check_overlap("b77_val_vs_test", val_s, test_s),
    ]:
        if n > 0:
            issues.append({"check": name, "count": n, "sample": sample})

    # WNUT-2017: identical token sequences across splits
    w17_dir = ROOT / "data" / "processed" / "wnut_2017"
    tr = set_from_parquet_tokens(w17_dir / "train.parquet")
    va = set_from_parquet_tokens(w17_dir / "validation.parquet")
    te = set_from_parquet_tokens(w17_dir / "test.parquet")

    for name, n, sample in [
        check_overlap("w17_train_vs_val", tr, va),
        check_overlap("w17_train_vs_test", tr, te),
        check_overlap("w17_val_vs_test", va, te),
    ]:
        if n > 0:
            issues.append({"check": name, "count": n, "sample": sample})

    result = {"ok": len(issues) == 0, "issues": issues}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 2)

if __name__ == "__main__":
    main()
