# scripts/text_norm.py
import re, unicodedata

SPACE_RE = re.compile(r"\s+")

def normalize_intent_text(text: str, lowercase=True, collapse_spaces=True, unicode_form="NFC", strip=True) -> str:
    if text is None:
        return ""
    t = unicodedata.normalize(unicode_form, text)
    if strip:
        t = t.strip()
    if collapse_spaces:
        t = SPACE_RE.sub(" ", t)
    if lowercase:
        t = t.lower()
    return t
