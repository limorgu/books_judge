"""
Build a CSV table from extracted page JSONs for quick review / spot-checking.

Reads:
  ~/Documents/books/inbox_photos/*.json

Writes:
  ~/Documents/books/extraction_table.csv

The table is meant for:
- checking coverage across the book
- spotting missing page numbers
- quickly previewing text quality
"""

import json
import csv
import re
from pathlib import Path

INBOX_DIR = Path.home() / "Documents" / "books" / "inbox_photos"
OUT_CSV = Path.home() / "Documents" / "books" / "extraction_table.csv"


def clean_preview(text: str, max_len: int = 180) -> str:
    """Single-line preview for table display."""
    if not text:
        return ""
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def main():
    if not INBOX_DIR.exists():
        raise FileNotFoundError(f"Missing inbox folder: {INBOX_DIR}")

    rows = []

    json_files = sorted(INBOX_DIR.glob("*.json"))
    if not json_files:
        print("No JSON files found — run extraction first.")
        return

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Skipping unreadable JSON: {jf.name} ({e})")
            continue

        rows.append({
            "source_file": data.get("source_file"),
            "book_name": data.get("book_name"),
            "title": data.get("title"),
            "page_number": data.get("page_number"),
            "text_length": len(data.get("text") or ""),
            "text_preview": clean_preview(data.get("text") or ""),
            "json_file": jf.name,
        })

    # Sort primarily by page number if available, otherwise by filename
    def sort_key(r):
        pn = r["page_number"]
        if isinstance(pn, int):
            return (0, pn)
        return (1, r["source_file"] or "")

    rows.sort(key=sort_key)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file",
                "book_name",
                "title",
                "page_number",
                "text_length",
                "text_preview",
                "json_file",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Saved table: {OUT_CSV}")
    print(f"Rows written: {len(rows)}")


if __name__ == "__main__":
    main()
