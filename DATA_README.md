# DATA_README

## Datasets (raw)
- **BANKING77** → `data/raw/banking77/{train.csv,test.csv,labels.json}`
  - Columns: `text`, `label` (int), `label_text` (string)
- **WNUT-2017** → `data/raw/wnut_2017/{train.jsonl,validation.jsonl,test.jsonl,labels.json}`
  - JSONL per line: `{"tokens": [..], "ner_tags": [..]}`; tag indices map to `labels.json`
- **CLINC OOS (optional small slice)** → `data/raw/clinc_oos/oos_test_small.csv`
  - Columns: `text`, `label` in `{"oos","in"}`

## Notes
- All raw exports are deterministic from Hugging Face Datasets.
- Do **not** modify files under `data/raw/`. Preprocessing outputs will go under `data/processed/`.
