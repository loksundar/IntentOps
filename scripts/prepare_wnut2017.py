# scripts/prepare_wnut2017.py
# Usage: python scripts/prepare_wnut2017.py
# Produces:
#   data/raw/wnut_2017/train.jsonl
#   data/raw/wnut_2017/validation.jsonl
#   data/raw/wnut_2017/test.jsonl
#   data/raw/wnut_2017/labels.json
from pathlib import Path
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "wnut_2017"
OUT.mkdir(parents=True, exist_ok=True)

# Canonical WNUT'17 labels (BIO + O)
LABELS = [
    "O",
    "B-corporation", "I-corporation",
    "B-creative-work", "I-creative-work",
    "B-group", "I-group",
    "B-location", "I-location",
    "B-person", "I-person",
    "B-product", "I-product",
]
LABEL2ID = {lbl: i for i, lbl in enumerate(LABELS)}

# Official source files (note test = emerging.test.annotated)
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
        return r.read().decode("utf-8", errors="strict")

def parse_conll_text(text: str):
    """
    Parse CoNLL-style data:
      - tokens and tags are whitespace-separated on each line
      - blank line = sentence boundary
      - lines starting with '#' are comments/metadata (ignored, no boundary)
      - if a tag contains ',' '|' or ';', keep the FIRST label (gold)
    Returns list of dicts: {"tokens": [...], "ner_tags": [int,...]}
    """
    sents = []
    tokens, tags = [], []
    for raw in text.splitlines():
        if not raw.strip():  # sentence/doc boundary
            if tokens:
                sents.append({"tokens": tokens, "ner_tags": [LABEL2ID[t] for t in tags]})
                tokens, tags = [], []
            continue
        if raw.lstrip().startswith("#"):
            # comment / metadata: ignore but DO NOT end the sentence
            continue
        parts = raw.split()
        if len(parts) < 2:
            # malformed row — skip defensively
            continue
        tok, tag = parts[0], parts[-1]

        # Normalize multi-label cells (e.g., "B-corporation,B-person,B-location")
        for sep in (",", "|", ";"):
            if sep in tag:
                tag = tag.split(sep)[0]
                break

        if tag not in LABEL2ID:
            raise RuntimeError(f"Unexpected tag '{tag}'. Update LABELS if needed.")
        tokens.append(tok)
        tags.append(tag)

    if tokens:
        sents.append({"tokens": tokens, "ner_tags": [LABEL2ID[t] for t in tags]})
    return sents

def convert(split: str, fname: str):
    # Prefer a pre-downloaded file under data/raw/wnut2017/ if present
    local_alt = ROOT / "data" / "raw" / "wnut2017" / fname  # optional manual drops
    if local_alt.exists():
        text = local_alt.read_text(encoding="utf-8")
    else:
        url = SRC[split][1]
        print(f"[WNUT-2017] Downloading {url}")
        text = _download(url)

    rows = parse_conll_text(text)
    out_path = OUT / f"{split}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[WNUT-2017] Wrote {out_path} ({len(rows)} records)")

def verify():
    # Quick checks: counts and label coverage
    import json
    def read_jsonl(p: Path):
        rows = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
        return rows

    paths = {
        "train": OUT / "train.jsonl",
        "validation": OUT / "validation.jsonl",
        "test": OUT / "test.jsonl",
    }
    counts = {k: len(read_jsonl(p)) for k, p in paths.items()}
    # Expected sentence counts when using gold test annotations
    expected = {"train": 3394, "validation": 1009, "test": 1287}

    # Label coverage
    seen = set()
    for split, p in paths.items():
        for row in read_jsonl(p):
            for tid in row["ner_tags"]:
                seen.add(tid)
    labels_seen = sorted(list(seen))
    print(f"[VERIFY] sentence counts: {counts}  (expected ~ {expected})")
    print(f"[VERIFY] unique label ids seen: {labels_seen}  (0..{len(LABELS)-1})")

    # Soft guards: warn (don’t fail) if significantly off
    def warn(msg): print(f"[VERIFY][WARN] {msg}")
    for k in expected:
        if abs(counts[k] - expected[k]) > 50:
            warn(f"{k} count {counts[k]} deviates far from expected {expected[k]}")

def main():
    for split, (fname, _) in SRC.items():
        convert(split, fname)
    (OUT / "labels.json").write_text(json.dumps(LABELS, indent=2), encoding="utf-8")
    print(f"[WNUT-2017] Wrote {(OUT / 'labels.json')} ({len(LABELS)} labels)")
    verify()

if __name__ == "__main__":
    main()
