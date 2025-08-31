# bin/normalize.py
import unicodedata, re

def normalize_text(s: str, lowercase: bool = True) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u200b", "")  # zero-width space
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower() if lowercase else s
