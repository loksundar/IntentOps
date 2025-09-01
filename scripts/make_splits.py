# scripts/make_splits.py
# Usage: python scripts/make_splits.py --config configs/config.yaml
import argparse, json, hashlib
from pathlib import Path
import yaml, pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from text_norm import normalize_intent_text

def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def process_banking77(cfg):
    c = cfg["datasets"]["banking77"]
    raw = Path(c["path_raw"])
    out = Path(c["path_out"])
    out.mkdir(parents=True, exist_ok=True)

    train_csv = raw / "train.csv"
    test_csv  = raw / "test.csv"
    labels_json = raw / "labels.json"

    train_df = pd.read_csv(train_csv)
    test_df  = pd.read_csv(test_csv)
    label_names = json.loads(labels_json.read_text(encoding="utf-8"))

    # id <-> text maps
    label_map_intent = { str(i): name for i, name in enumerate(label_names) }
    label_map_intent_inv = { name: i for i, name in enumerate(label_names) }

    def prep(df):
        # ensure label_text and label id exist
        if "label_text" not in df.columns and "label" in df.columns:
            df["label_text"] = df["label"].apply(lambda i: label_map_intent[str(int(i))])
        if "label" not in df.columns and "label_text" in df.columns:
            df["label"] = df["label_text"].map(label_map_intent_inv).astype(int)

        df["text_norm"] = df["text"].astype(str).apply(
            lambda t: normalize_intent_text(
                t,
                lowercase=c["text_normalization"]["lowercase"],
                collapse_spaces=c["text_normalization"]["collapse_spaces"],
                unicode_form=c["text_normalization"]["unicode_form"],
                strip=c["text_normalization"]["strip"],
            )
        )
        return df[["text_norm", "label", "label_text"]].rename(
            columns={"text_norm": "text", "label": "intent_id", "label_text": "intent_label"}
        )

    train_df = prep(train_df)
    test_df  = prep(test_df)

    if c.get("resplit_all", False):
        # Combine, DEDUPE on (text, intent_id) to kill cross-split duplicates
        all_df = pd.concat([train_df, test_df], ignore_index=True)
        before = len(all_df)
        all_df = all_df.drop_duplicates(subset=["text", "intent_id"]).reset_index(drop=True)
        after = len(all_df)
        if before != after:
            print(f"[BANKING77] Deduped {before - after} duplicate rows across splits.")

        y = all_df["intent_id"].values

        # First pick TEST
        test_size = c.get("test_fraction", 0.10)
        sss1 = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=cfg["random_seed"])
        idx_all = list(range(len(all_df)))
        idx_trainval, idx_test = next(sss1.split(idx_all, y))
        df_trainval = all_df.iloc[idx_trainval].reset_index(drop=True)
        df_test     = all_df.iloc[idx_test].reset_index(drop=True)

        # Then pick VAL from train+val
        val_size = c.get("val_fraction", 0.10)
        # relative fraction inside train+val
        rel_val = val_size / (1.0 - test_size)
        sss2 = StratifiedShuffleSplit(n_splits=1, test_size=rel_val, random_state=cfg["random_seed"])
        y_trainval = df_trainval["intent_id"].values
        idx_train, idx_val = next(sss2.split(df_trainval, y_trainval))
        df_train = df_trainval.iloc[idx_train].reset_index(drop=True)
        df_val   = df_trainval.iloc[idx_val].reset_index(drop=True)

    else:
        # Keep canonical test; stratify a val from train
        y = train_df["intent_id"].values
        sss = StratifiedShuffleSplit(n_splits=1, test_size=c["val_fraction"], random_state=cfg["random_seed"])
        idx_train, idx_val = next(sss.split(train_df, y))
        df_train = train_df.iloc[idx_train].reset_index(drop=True)
        df_val   = train_df.iloc[idx_val].reset_index(drop=True)
        df_test  = test_df

    # Write CSVs
    df_train.to_csv(out / "train.csv", index=False)
    df_val.to_csv(out / "val.csv", index=False)
    df_test.to_csv(out / "test.csv", index=False)

    return {
        "label_map_intent": label_map_intent,
        "files": {
            "train": str((out / "train.csv").as_posix()),
            "val":   str((out / "val.csv").as_posix()),
            "test":  str((out / "test.csv").as_posix()),
        },
        "raw_md5": {
            "train.csv": md5_file(train_csv),
            "test.csv":  md5_file(test_csv),
            "labels.json": md5_file(labels_json)
        }
    }

def process_wnut(cfg):
    from pyarrow import parquet as pq  # noqa: F401  (ensures pyarrow installed)
    raw = Path(cfg["datasets"]["wnut_2017"]["path_raw"])
    out = Path(cfg["datasets"]["wnut_2017"]["path_out"])
    out.mkdir(parents=True, exist_ok=True)
    labels = json.loads((raw / "labels.json").read_text(encoding="utf-8"))
    label_map_ner = { str(i): tag for i, tag in enumerate(labels) }

    def load_jsonl(p: Path):
        rows = []
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                rows.append({"tokens": obj["tokens"], "tags": obj["ner_tags"]})
        return pd.DataFrame(rows)

    splits = {}
    for split in ["train", "validation", "test"]:
        df = load_jsonl(raw / f"{split}.jsonl")
        path = out / f"{split}.parquet"
        df.to_parquet(path, index=False)
        splits[split] = str(path.as_posix())

    return {
        "label_map_ner": label_map_ner,
        "files": splits,
        "raw_md5": {
            "train.jsonl": md5_file(raw / "train.jsonl"),
            "validation.jsonl": md5_file(raw / "validation.jsonl"),
            "test.jsonl": md5_file(raw / "test.jsonl"),
            "labels.json": md5_file(raw / "labels.json"),
        }
    }

def process_clinc_oos(cfg):
    c = cfg["datasets"].get("clinc_oos", {})
    if not c or not c.get("enabled", False):
        return None
    raw_dir = Path(c["path_raw"])
    src = raw_dir / "oos_test_small.csv"
    if not src.exists():
        print("[CLINC_OOS] Skipping (raw slice not present)")
        return None

    out_dir = Path(c["path_out"]); out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(src)
    # Normalize like intent text
    df["text"] = df["text"].astype(str).apply(
        lambda t: normalize_intent_text(
            t,
            lowercase=True,
            collapse_spaces=True,
            unicode_form="NFC",
            strip=True,
        )
    )
    df["oos_flag"] = (df["label"].astype(str).str.lower() == "oos").astype(int)
    out = out_dir / "test.csv"
    df[["text", "oos_flag"]].to_csv(out, index=False)

    return {
        "files": {"test": str(out.as_posix())},
        "raw_md5": {"oos_test_small.csv": md5_file(src)}
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    manifest = {"seed": cfg["random_seed"], "artifacts": {}}

    b77 = process_banking77(cfg)
    w17 = process_wnut(cfg)
    coo = process_clinc_oos(cfg)

    # Save label maps
    save_json(b77["label_map_intent"], Path(cfg["outputs"]["label_map_intent"]))
    save_json(w17["label_map_ner"],    Path(cfg["outputs"]["label_map_ner"]))

    manifest["artifacts"]["banking77"] = b77
    manifest["artifacts"]["wnut_2017"] = w17
    if coo:
        manifest["artifacts"]["clinc_oos"] = coo

    save_json(manifest, Path(cfg["outputs"]["manifest"]))
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
