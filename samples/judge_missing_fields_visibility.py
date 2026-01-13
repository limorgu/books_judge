"""
Judge whether missing fields (book_name/title/page_number) are actually VISIBLE in the image.

Reads extracted JSON sidecars from:
  ~/Documents/books/inbox_photos/*.json

For pages where any of book_name/title/page_number is missing (null/empty),
it asks the model: is the field visible on the page?

Writes:
  ~/Documents/books/judge_missing_visibility.json
"""

import json
import io
import base64
import os
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image
from openai import OpenAI

INBOX_DIR = Path.home() / "Documents" / "books" / "inbox_photos"
OUT_PATH = Path.home() / "Documents" / "books" / "judge_missing_visibility.json"
MODEL = "gpt-4o-mini"

client = OpenAI()


def is_missing(v: Any) -> bool:
    return v is None or v == "" or v == "null"


def image_to_data_url_under_5mb(path: Path, max_bytes: int = 5 * 1024 * 1024) -> str:
    """
    Convert image to a JPEG data URL under 5MB.
    (Simple compression; enough for judge visibility.)
    """
    img = Image.open(path).convert("RGB")

    def encode(q: int) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        return buf.getvalue()

    quality = 85
    data = encode(quality)

    if len(data) > max_bytes:
        quality = 65
        data = encode(quality)

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def judge_visibility(image_path: Path, extracted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns strict JSON:
    {
      "book_name_visible": bool,
      "title_visible": bool,
      "page_number_visible": bool,
      "notes": str
    }
    """
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "book_name_visible": {"type": "boolean"},
            "title_visible": {"type": "boolean"},
            "page_number_visible": {"type": "boolean"},
            "notes": {"type": "string"},
        },
        "required": ["book_name_visible", "title_visible", "page_number_visible", "notes"],
    }

    prompt = (
        "You are checking whether specific metadata is LITERALLY VISIBLE in the photo of a book page.\n"
        "Do NOT guess or infer from the body text.\n"
        "Mark a field true ONLY if you can actually see it printed on the page.\n\n"
        "Fields:\n"
        "- book_name_visible: the book title/name (e.g., on a header/cover/page)\n"
        "- title_visible: a chapter/section title (e.g., 'Three', 'Chapter 3')\n"
        "- page_number_visible: the page number\n\n"
        "If something is cut off, blurry, or not shown, mark false.\n"
        "Return strict JSON only."
    )

    data_url = image_to_data_url_under_5mb(image_path)

    resp = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_text",
                        "text": "EXTRACTED_JSON:\n" + json.dumps(extracted, ensure_ascii=False),
                    },
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "visibility_check",
                "strict": True,
                "schema": schema,
            }
        },
    )

    return json.loads(resp.output_text)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set. Run: export OPENAI_API_KEY='...'")

    if not INBOX_DIR.exists():
        raise FileNotFoundError(f"Missing inbox folder: {INBOX_DIR}")

    results: List[Dict[str, Any]] = []

    json_files = sorted(INBOX_DIR.glob("*.json"))
    if not json_files:
        print("No JSON files found. Run extraction first.")
        return

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Skip unreadable JSON: {jf.name} ({e})")
            continue

        missing_fields = [k for k in ["book_name", "title", "page_number"] if is_missing(data.get(k))]
        if not missing_fields:
            continue

        source_file = data.get("source_file") or jf.name[:-5]  # strip ".json"
        img_path = INBOX_DIR / source_file
        if not img_path.exists():
            print(f"Skip (image missing): {source_file}")
            continue

        print(f"Judging visibility: {img_path.name}  missing={missing_fields}")
        vis = judge_visibility(img_path, data)

        results.append(
            {
                "image": img_path.name,
                "json_file": jf.name,
                "missing_fields": missing_fields,
                **vis,
            }
        )

    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")
    print(f"Judged pages: {len(results)}")


if __name__ == "__main__":
    main()
