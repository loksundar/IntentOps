# scripts/prepare_wnut2017.py
from pathlib import Path
import json, urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "wnut_2017"
OUT.mkdir(parents=True, exist_ok=True)

LABELS = [
    "O",
    "B-corporation","I-corporation",
    "B-creative-work","I-creative-work",
    "B-group","I-group",
    "B-location","I-location",
    "B-person","I-person",
    "B-product","I-product",
]
LABEL2ID = {lbl: i for i, lbl in enumerate(LABELS)}

SRC = {
    "train": ("wnut17train.conll",
              "https://raw.githubusercontent.com/leondz/emerging_entities_17/master/wnut17train.conll"),
    "validation": ("emerging.dev.conll",
                   "https://raw.githubusercontent.com/leondz/emerging_entities_17/master/emerging.dev.conll"),
    "test": ("emerging.test.annotated",
             "https://raw.githubusercontent.com/leondz/emerging_entities_17/master/emerging.test.annotated"),
}

def _download(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8")

def parse_conll_text(text: str):
    """
    - blank line = boundary
    - comment line ('#' at start) = boundary IF we have tokens collected
    - multi-label cell like 'B-corporation,B-person' -> keep the first
    """
    sents, tokens, tags = [], [], []
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            if tokens:
                sents.append({"tokens": tokens, "ner_tags": [LABEL2ID[t] for t in tags]})
                tokens, tags = [], []
            continue
        if line.lstrip().startswith("#"):
            # treat comments as sentence/document boundary
            if tokens:
                sents.append({"tokens": tokens, "ner_tags": [LABEL2ID[t] for t in tags]})
                tokens, tags = [], []
            continue
        parts = line.split()
        if len(parts) < 2:
            # rare malformed row; skip
            continue
        tok, tag = parts[0], parts[-1]
        for sep in (",","|",";"):
            if sep in tag:
                tag = tag.split(sep)[0]
                break
        if tag not in LABEL2ID:
            raise RuntimeError(f"Unexpected tag '{tag}'")
        tokens.append(tok)
        tags.append(tag)
    if tokens:
        sents.append({"tokens": tokens, "ner_tags": [LABEL2ID[t] for t in tags]})
    return sents

def convert(split: str, fname: str):
    local_alt = ROOT / "data" / "raw" / "wnut2017" / fname
    text = local_alt.read_text(encoding="utf-8") if local_alt.exists() else _download(SRC[split][1])
    rows = parse_conll_text(text)
    out_path = OUT / f"{split}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[WNUT-2017] Wrote {out_path} ({len(rows)} records)")

def verify():
    def count_jsonl(p: Path) -> int:
        n=0
        with p.open("r", encoding="utf-8") as f:
            for _ in f: n+=1
        return n
    counts = {
        "train": count_jsonl(OUT/"train.jsonl"),
        "validation": count_jsonl(OUT/"validation.jsonl"),
        "test": count_jsonl(OUT/"test.jsonl"),
    }
    print(f"[VERIFY] counts: {counts} (expected ~ {{'train': 3394,'validation':1009,'test':1287}})")

def main():
    for split, (fname, _) in SRC.items():
        convert(split, fname)
    (OUT/"labels.json").write_text(json.dumps(LABELS, indent=2), encoding="utf-8")
    print(f"[WNUT-2017] Wrote {(OUT/'labels.json')}")
    verify()

if __name__ == "__main__":
    main()
