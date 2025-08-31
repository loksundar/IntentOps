# bin/fetch_banking77.py
from datasets import load_dataset
import pandas as pd
from pathlib import Path
import json, urllib.request

raw_dir = Path("data/raw/banking77")
raw_dir.mkdir(parents=True, exist_ok=True)

# --- Load the data in a script-free way ---
try:
    # Fastest path: parquet mirror (columns: 'utterance', 'label')
    ds = load_dataset("DeepPavlov/banking77")  # splits: train, test
    text_col = "text" if "text" in ds["train"].column_names else "utterance"
except Exception:
    # Fallback: load raw CSVs directly from PolyAI GitHub
    data_files = {
        "train": "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/train.csv",
        "test":  "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv",
    }
    ds = load_dataset("csv", data_files=data_files)
    text_col = "text"

# --- Get readable intent names (works for both sources) ---
def get_label_names_from_ds(dataset):
    try:
        feat = dataset["train"].features["label"]
        names = getattr(feat, "names", None)
        if names:
            return list(names)
    except Exception:
        pass
    # Fallback: read mapping from PolyAI's dataset_infos.json on the Hub
    url = "https://huggingface.co/datasets/PolyAI/banking77/resolve/main/dataset_infos.json"
    with urllib.request.urlopen(url, timeout=10) as r:
        infos = json.load(r)
    return infos["default"]["features"]["label"]["names"]

label_names = get_label_names_from_ds(ds)

def dump(split):
    df = ds[split].to_pandas()
    # unify to 'text' column name
    if text_col != "text":
        df = df.rename(columns={text_col: "text"})
    # ensure numeric label then map to readable intent
    df["intent_id"] = df["label"].astype(int)
    df["intent"] = df["intent_id"].apply(lambda i: label_names[i])
    out = df[["text", "intent", "intent_id"]]
    out.to_csv(raw_dir / f"{split}.csv", index=False)

dump("train")
dump("test")
print("BANKING77 saved -> data/raw/banking77/train.csv, test.csv")
