import re, pathlib, shutil

phone = re.compile(r'(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}(?!\d)')

def redact_digits(s: str) -> str:
    return ''.join('X' if ch.isdigit() else ch for ch in s)

def redact_text(text: str) -> tuple[str,int]:
    count = 0
    def repl(m):
        nonlocal count
        count += 1
        return redact_digits(m.group(0))
    return phone.sub(repl, text), count

path = pathlib.Path("data/raw/wnut2017/wnut17train.conll")
text = path.read_text(encoding="utf-8", errors="ignore")
new_text, n = redact_text(text)

if n > 0:
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copyfile(path, backup)
    path.write_text(new_text, encoding="utf-8")
    print(f"Redacted {n} phone-like strings. Backup at {backup}")
else:
    print("No phone-like strings found; nothing to redact.")