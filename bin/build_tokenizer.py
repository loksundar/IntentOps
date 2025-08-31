# bin/build_tokenizer.py
import json
from pathlib import Path
import ujson

NER_DIR = Path("data/processed/wnut2017")
TOK_DIR = Path("data/processed/tokenizers"); TOK_DIR.mkdir(parents=True, exist_ok=True)

MIN_FREQ = 1  # keep everything for now; tune later
PAD, UNK = "<pad>", "<unk>"

def read_jsonl(path: Path):
    for line in path.open(encoding="utf-8"):
        yield ujson.loads(line)

def build_word_vocab():
    from collections import Counter
    ctr = Counter()
    for split in ["train.jsonl"]:
        for ex in read_jsonl(NER_DIR / split):
            ctr.update(ex["tokens"])
    vocab = [PAD, UNK] + [w for w,c in ctr.items() if c >= MIN_FREQ]
    word2id = {w:i for i,w in enumerate(vocab)}
    return {"vocab": vocab, "word2id": word2id}

def build_char_vocab(word_vocab):
    chars = {PAD, UNK}
    for w in word_vocab["vocab"]:
        chars.update(list(w))
    chars = [PAD, UNK] + sorted(ch for ch in chars if ch not in {PAD, UNK})
    char2id = {ch:i for i,ch in enumerate(chars)}
    return {"chars": chars, "char2id": char2id}

def main():
    word_vocab = build_word_vocab()
    char_vocab = build_char_vocab(word_vocab)
    (TOK_DIR / "word_vocab.json").write_text(json.dumps(word_vocab, ensure_ascii=False, indent=2), encoding="utf-8")
    (TOK_DIR / "char_vocab.json").write_text(json.dumps(char_vocab, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update config
    cfg = Path("data/processed/config.yaml")
    curr = cfg.read_text(encoding="utf-8") if cfg.exists() else "seed: 42\n"
    curr += (
        "tokenizer:\n"
        f"  ner_word_min_freq: {MIN_FREQ}\n"
        "  specials:\n"
        f"    pad: {PAD}\n"
        f"    unk: {UNK}\n"
        "artifacts:\n"
        "  intent_label_map: data/processed/label_maps/intent_label_map.json\n"
        "  ner_label_map: data/processed/label_maps/ner_label_map.json\n"
        "  ner_word_vocab: data/processed/tokenizers/word_vocab.json\n"
        "  ner_char_vocab: data/processed/tokenizers/char_vocab.json\n"
    )
    cfg.write_text(curr, encoding="utf-8")
    print("Tokenizers built -> data/processed/tokenizers")

if __name__ == "__main__":
    main()
