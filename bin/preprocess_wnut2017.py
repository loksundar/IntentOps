# bin/preprocess_wnut2017.py
import json
from pathlib import Path
from normalize import normalize_text

RAW = Path("data/raw/wnut2017")
OUT = Path("data/processed/wnut2017"); OUT.mkdir(parents=True, exist_ok=True)
LM_DIR = Path("data/processed/label_maps"); LM_DIR.mkdir(parents=True, exist_ok=True)

# Decision: preserve case for NER (case carries signal)
LOWERCASE = False
SEED = 42  # kept for consistency in config.yaml

def read_conll(path: Path):
    sents = []
    tokens, tags = [], []
    with path.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                if tokens:
                    sents.append({"tokens": tokens, "tags": tags})
                    tokens, tags = [], []
                continue
            # Format: TOKEN \t TAG  or "TOKEN TAG"
            parts = line.split()
            if len(parts) < 2:
                # some lines might be stray; skip safely
                continue
            tok, tag = parts[0], parts[-1]
            tok = normalize_text(tok, lowercase=LOWERCASE)
            tokens.append(tok)
            tags.append(tag)
    if tokens:
        sents.append({"tokens": tokens, "tags": tags})
    return sents

def write_jsonl(items, path: Path):
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def collect_tagset(sents):
    tags = set()
    for s in sents:
        for t in s["tags"]:
            tags.add(t)
    return sorted(tags)

def main():
    train_sents = read_conll(RAW / "wnut17train.conll")
    val_sents   = read_conll(RAW / "emerging.dev.conll")   # dev → val
    test_sents  = read_conll(RAW / "emerging.test.conll")

    # Save JSONL
    write_jsonl(train_sents, OUT / "train.jsonl")
    write_jsonl(val_sents,   OUT / "val.jsonl")
    write_jsonl(test_sents,  OUT / "test.jsonl")

    # Label map for BIO tags
    tagset = sorted(set(collect_tagset(train_sents) + collect_tagset(val_sents) + collect_tagset(test_sents)))
    tag2id = {t:i for i,t in enumerate(tagset)}
    with open(LM_DIR / "ner_label_map.json", "w", encoding="utf-8") as f:
        json.dump({"tags": tagset, "tag2id": tag2id}, f, ensure_ascii=False, indent=2)

    # Append to config
    cfg = Path("data/processed/config.yaml")
    curr = cfg.read_text(encoding="utf-8") if cfg.exists() else "seed: 42\n"
    curr += (
        "wnut2017:\n"
        f"  lowercase: {str(LOWERCASE).lower()}\n"
        "  format: jsonl\n"
        "  splits:\n"
        "    train: wnut17train.conll\n"
        "    val: emerging.dev.conll\n"
        "    test: emerging.test.conll\n"
    )
    cfg.write_text(curr, encoding="utf-8")
    print("WNUT-2017 processed -> data/processed/wnut2017 (train/val/test JSONL)")

if __name__ == "__main__":
    main()
