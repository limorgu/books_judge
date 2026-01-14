"""
Extract book page fields from images under:
  ~/Documents/books/inbox_photos/**/<image>.jpg

Folder structure requirement:
  inbox_photos/
    Book_Name_Author_Name/
      IMG_001.jpg
      IMG_002.jpg
      ...

We read book_name + author_name from the folder name (NOT the model),
and extract text + optional title/page_number from the image.

Requires:
  pip install openai pillow
Env:
  export OPENAI_API_KEY="..."
"""

import os
import json
import io
import base64
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image
from openai import OpenAI

ROOT_DIR = Path.home() / "Documents" / "books" / "inbox_photos"
OUT_SUFFIX = ".json"

MODEL = "gpt-4o-mini"  # supports vision + structured output


IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None or x == "":
            return None
        return int(x)
    except Exception:
        return None


def _normalize_token(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _smart_title_case(s: str) -> str:
    # Keeps simple readability without mangling acronyms too much.
    # You can swap to `.title()` if you prefer.
    return " ".join(w.capitalize() if w.islower() else w for w in s.split())


def parse_book_author_from_folder(image_path: Path) -> Tuple[str, str]:
    """
    Expected:
      .../inbox_photos/<book_name>_<author_name>/<image>.jpg

    Example folder:
      It's_just_your_imagination_revital_shiri_horowitz

    Heuristic:
      - If you have EXACTLY two books, you can replace this with a mapping dictionary.
      - Otherwise, we split the folder into tokens and assume the last 3 tokens are author,
        everything before is book name (works for many "First Last Last" author formats).

    You can tune AUTHOR_TOKENS below if your authors are usually 2 tokens.
    """
    folder = image_path.parent.name

    # Normalize separators
    folder = folder.replace("-", "_")
    parts = [p for p in folder.split("_") if p]

    AUTHOR_TOKENS = 3  # change to 2 if your authors are usually 2 words

    if len(parts) >= AUTHOR_TOKENS + 1:
        author = " ".join(parts[-AUTHOR_TOKENS:])
        book = " ".join(parts[:-AUTHOR_TOKENS])
    else:
        # fallback: if folder doesn't match expectation
        book = " ".join(parts)
        author = ""

    book = _smart_title_case(_normalize_token(book))
    author = _smart_title_case(_normalize_token(author)) if author else ""

    return book, author


def image_to_data_url_under_5mb(path: Path, max_bytes: int = 5 * 1024 * 1024) -> str:
    """Return a data URL (jpeg) resized/compressed to stay <= 5MB."""
    img = Image.open(path).convert("RGB")

    def encode(im: Image.Image, q: int) -> bytes:
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=q, optimize=True)
        return buf.getvalue()

    quality = 90
    data = encode(img, quality)

    # Compress
    while len(data) > max_bytes and quality > 55:
        quality -= 7
        data = encode(img, quality)

    # Downscale if still too big
    while len(data) > max_bytes:
        w, h = img.size
        img = img.resize((int(w * 0.85), int(h * 0.85)))
        data = encode(img, min(85, quality))
        if img.size[0] < 400 or img.size[1] < 400:
            break

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def extract_one_image(client: OpenAI, image_path: Path) -> Dict[str, Any]:
    # We only ask the model for what is on the page (NOT book/author)
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "page_number": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "text": {"type": "string"},
        },
        "required": ["title", "page_number", "text"],
    }

    data_url = image_to_data_url_under_5mb(image_path)

    resp = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Extract the visible page text accurately.\n\n"
                            "Return:\n"
                            "- title: ONLY if a page/chapter/section title is printed on this page; otherwise null\n"
                            "- page_number: ONLY if a page number is visible; otherwise null\n"
                            "- text: the exact page text, preserving paragraph breaks with \\n\n\n"
                            "Do NOT guess missing fields."
                        ),
                    },
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "book_page_extract",
                "strict": True,
                "schema": schema,
            }
        },
    )

    parsed = json.loads(resp.output_text)

    return {
        "title": parsed.get("title", None),
        "page_number": _safe_int(parsed.get("page_number", None)),
        "text": (parsed.get("text", "") or ""),
    }


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set. Run: export OPENAI_API_KEY='...'")

    if not ROOT_DIR.exists():
        raise FileNotFoundError(f"Missing folder: {ROOT_DIR}")

    client = OpenAI()

    # ✅ recursively find images inside subfolders
    images = [
        p for p in sorted(ROOT_DIR.rglob("*"))
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    ]

    if not images:
        print(f"No images found under {ROOT_DIR}")
        return

    for img in images:
        out_path = img.with_suffix(img.suffix + OUT_SUFFIX)  # IMG.jpg.json
        if out_path.exists():
            print(f"Skip (already has JSON): {out_path}")
            continue

        book_name, author_name = parse_book_author_from_folder(img)

        print(f"Extracting: {img}")
        page = extract_one_image(client, img)

        # Build final JSON (book/author from folder, rest from model)
        data = {
            "book_name": book_name,
            "author": author_name or None,
            "title": page.get("title"),
            "page_number": page.get("page_number"),
            "text": page.get("text"),
            "source_file": img.name,
            "reference": str(img),
        }

        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {out_path}")

    print("Done.")


if __name__ == "__main__":
    main()
