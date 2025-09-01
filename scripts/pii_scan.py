# bin/pii_scan.py
import re, sys
from pathlib import Path

ROOT = Path("data/raw")
patterns = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}(?!\d)")
}

def scan_file(p: Path):
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return {"error": str(e)}
    counts = {k: len(r.findall(text)) for k, r in patterns.items()}
    return counts

def main():
    exts = {".txt", ".csv", ".json", ".conll", ".tsv"}
    totals = {"email":0, "phone":0}
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            counts = scan_file(p)
            if "error" in counts:
                print(f"[SKIP] {p} ({counts['error']})")
                continue
            totals["email"] += counts["email"]
            totals["phone"] += counts["phone"]
            print(f"{p}: emails={counts['email']}, phones={counts['phone']}")
    print(f"\nTOTAL: emails={totals['email']}, phones={totals['phone']}")
    # Exit 0 always; we just log counts for review per Safety Gate
    sys.exit(0)

if __name__ == "__main__":
    main()
