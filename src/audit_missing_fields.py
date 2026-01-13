import json
from pathlib import Path

INBOX_DIR = Path.home() / "Documents" / "books" / "inbox_photos"

def main():
    missing = []
    for jf in sorted(INBOX_DIR.glob("*.json")):
        data = json.loads(jf.read_text(encoding="utf-8"))
        missing_fields = []
        for k in ["book_name", "title", "page_number"]:
            if data.get(k) in [None, "", "null"]:
                missing_fields.append(k)
        if missing_fields:
            missing.append({
                "json": jf.name,
                "image": data.get("source_file", jf.name.replace(".json","")),
                "missing": missing_fields
            })

    print(f"Total JSON files: {len(list(INBOX_DIR.glob('*.json')))}")
    print(f"Files with missing fields: {len(missing)}\n")

    # Print a short report
    for row in missing[:30]:
        print(f"{row['image']}  -> missing: {', '.join(row['missing'])}  (json: {row['json']})")

    if len(missing) > 30:
        print(f"\n...and {len(missing)-30} more")

if __name__ == "__main__":
    main()
