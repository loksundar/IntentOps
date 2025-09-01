# scripts/download_datasets.py
# Usage: python scripts/download_datasets.py
# Exports:
#   - BANKING77 -> data/raw/banking77/{train,test}.csv (+labels.json)
#   - CLINC OOS (plus, small slice) -> data/raw/clinc_oos/oos_test_small.csv
import json
from pathlib import Path
import pandas as pd
from datasets import load_dataset, DownloadMode

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CACHE_DIR = ROOT / "data" / ".hf_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

B77 = RAW / "banking77"
WN = RAW / "wnut_2017"
CO = RAW / "clinc_oos"
B77.mkdir(parents=True, exist_ok=True)
WN.mkdir(parents=True, exist_ok=True)
CO.mkdir(parents=True, exist_ok=True)


def export_banking77():
    ds = load_dataset(
        "banking77",
        cache_dir=str(CACHE_DIR),
        download_mode=DownloadMode.REUSE_DATASET_IF_EXISTS,
    )
    for split in ds.keys():  # train, test
        df = pd.DataFrame(ds[split])
        cols = [c for c in df.columns if c in ("text", "label", "label_text")]
        df = df[cols]
        out = B77 / f"{split}.csv"
        df.to_csv(out, index=False, encoding="utf-8")
        print(f"[BANKING77] Wrote {out} ({len(df)} rows)")
    labels = ds["train"].features["label"].names
    (B77 / "labels.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")

def export_clinc_oos_small():
    """
    Export a small OOS slice from the CLINC OOS dataset ('plus' config).
    Writes data/raw/clinc_oos/oos_test_small.csv with columns: text, label.
    """
    try:
        ds = load_dataset(
            "clinc_oos",
            "plus",  # requires a config: 'small' | 'plus' | 'imbalanced'
            cache_dir=str(CACHE_DIR),
            download_mode=DownloadMode.REUSE_DATASET_IF_EXISTS,
        )
    except Exception as e:
        print(f"[CLINC_OOS] Skipping (dataset not available): {e}")
        return

    rows = []
    test = ds["test"]
    for rec in test:
        text = rec.get("text") or rec.get("utterance") or ""
        intent = str(rec.get("intent"))
        # normalize: mark 'oos' as out-of-scope, everything else as 'in'
        is_oos = (intent.lower() == "oos") or bool(rec.get("oos", False))
        rows.append({"text": text, "label": "oos" if is_oos else "in"})
    df = pd.DataFrame(rows).head(2000)  # keep it compact
    out = CO / "oos_test_small.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"[CLINC_OOS] Wrote {out} ({len(df)} rows)")


if __name__ == "__main__":
    export_banking77()
    export_clinc_oos_small()
    print("Done.")
