import json
from pathlib import Path

INBOX_DIR = Path.home() / "Documents" / "books" / "inbox_photos"

def main():
    bad = []
    json_files = sorted(INBOX_DIR.glob("*.json"))
    for jf in json_files:
        try:
            txt = jf.read_text(encoding="utf-8")
            json.loads(txt)
        except Exception as e:
            bad.append((jf.name, str(e)))

    print(f"Total JSON files: {len(json_files)}")
    print(f"Bad JSON files: {len(bad)}\n")

    for name, err in bad[:50]:
        print(f"{name} -> {err}")

    if len(bad) > 50:
        print(f"\n...and {len(bad)-50} more")

if __name__ == "__main__":
    main()
