# DATA_README — Raw Schemas

## banking77 (CSV)
- Files: `data/raw/banking77/train.csv`, `test.csv`
- Columns:
  - `text` (str): user utterance
  - `intent` (str): human-readable label
  - `intent_id` (int): label index (0..76)

## wnut2017 (CoNLL)
- Files: `wnut17train.conll`, `emerging.dev.conll`, `emerging.test.conll`
- Format: one token per line: `token  tag`, sentences separated by blank lines. Tags use BIO scheme over entity types:
  `PER, LOC, GRP, CW, CORP, PROD` (with B-/I- prefixes).

## clinc_oos (JSON, optional)
- Files: `data_full.json`, `data_oos_plus.json`
- Format (per CLINC repo): `train/val/test` contain in-scope utterances grouped by intent; `oos_*` contain OOS utterances.
