# bin/preprocess_banking77.py
import json
from pathlib import Path
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from normalize import normalize_text

SEED = 42
VAL_FRACTION = 0.1
LOWERCASE = True

RAW_DIR = Path("data/raw/banking77")
OUT_DIR = Path("data/processed/banking77"); OUT_DIR.mkdir(parents=True, exist_ok=True)
LM_DIR = Path("data/processed/label_maps"); LM_DIR.mkdir(parents=True, exist_ok=True)

def load_split(name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / f"{name}.csv")
    assert {"text","intent","intent_id"}.issubset(df.columns), f"Missing columns in {name}.csv"
    df["text_norm"] = df["text"].apply(lambda s: normalize_text(s, lowercase=LOWERCASE))
    return df

def group_stratified_val_split(df_train: pd.DataFrame, val_frac: float, seed: int):
    groups = df_train["text_norm"].values  # keep identical utterances within the same split
    gss = GroupShuffleSplit(n_splits=1, test_size=val_frac, random_state=seed)
    idx_train, idx_val = next(gss.split(df_train, groups=groups))
    return df_train.iloc[idx_train].copy(), df_train.iloc[idx_val].copy()

def main():
    train = load_split("train")
    test  = load_split("test")

    # NEW: drop any train rows whose normalized text appears in test (avoid leakage)
    test_norms = set(test["text_norm"])
    before = len(train)
    train = train[~train["text_norm"].isin(test_norms)].copy()
    dropped = before - len(train)

    # Split train -> train/val (group-aware)
    train_new, val = group_stratified_val_split(train, VAL_FRACTION, SEED)

    # Label map from original order present in train (77 intents expected)
    id2label = train[["intent_id","intent"]].drop_duplicates().sort_values("intent_id")
    label_list = id2label["intent"].tolist()
    label2id = {lbl:i for i,lbl in enumerate(label_list)}

    for df in (train_new, val, test):
        df["intent_id"] = df["intent"].map(label2id)

    # Save processed CSV/Parquet
    for name, df in [("train", train_new), ("val", val), ("test", test)]:
        cols = ["text","text_norm","intent","intent_id"]
        df[cols].to_csv(OUT_DIR / f"{name}.csv", index=False)
        try:
            df[cols].to_parquet(OUT_DIR / f"{name}.parquet", index=False)
        except Exception:
            pass

    # Save label map
    with open(LM_DIR / "intent_label_map.json", "w", encoding="utf-8") as f:
        json.dump({"labels": label_list, "label2id": label2id}, f, ensure_ascii=False, indent=2)

    # Save/update config + dedup note
    cfg_path = Path("data/processed/config.yaml")
    cfg = ""
    if cfg_path.exists():
        cfg = cfg_path.read_text(encoding="utf-8")
    else:
        cfg = "seed: 42\n"
    cfg += (
        "banking77:\n"
        f"  lowercase: {str(LOWERCASE).lower()}\n"
        f"  val_fraction: {VAL_FRACTION}\n"
        f"  dropped_train_due_to_test_overlap: {dropped}\n"
    )
    cfg_path.write_text(cfg, encoding="utf-8")

    print(f"BANKING77 processed. Dropped {dropped} train rows overlapping test.")

if __name__ == "__main__":
    main()
