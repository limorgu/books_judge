"""
Extract book page fields from images in ~/Documents/books/inbox_photos
using OpenAI vision + Structured Outputs, and save a sidecar JSON per image.

Requires:
  pip install openai pillow
Env:
  export OPENAI_API_KEY="..."
"""

import os, json, io, base64
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image
from openai import OpenAI

INBOX_DIR = Path.home() / "Documents" / "books" / "inbox_photos"
OUT_SUFFIX = ".json"

MODEL = "gpt-4o-mini"  # fast + cheap + supports vision + structured output


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def image_to_data_url_under_5mb(path: Path, max_bytes: int = 5 * 1024 * 1024) -> str:
    """Return a data URL (jpeg) resized/compressed to stay <= 5MB."""
    img = Image.open(path).convert("RGB")

    def encode(im: Image.Image, q: int) -> bytes:
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=q, optimize=True)
        return buf.getvalue()

    quality = 90
    data = encode(img, quality)

    while len(data) > max_bytes and quality > 55:
        quality -= 7
        data = encode(img, quality)

    while len(data) > max_bytes:
        w, h = img.size
        img = img.resize((int(w * 0.85), int(h * 0.85)))
        data = encode(img, min(85, quality))
        if img.size[0] < 400 or img.size[1] < 400:
            break

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def extract_one_image(client: OpenAI, image_path: Path) -> Dict[str, Any]:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "book_name": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "title": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            "page_number": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
            "text": {"type": "string"},
            "source_file": {"type": "string"},
        },
        "required": ["book_name", "title", "page_number", "text", "source_file"],
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
                            "Extract the visible page text accurately. "
                            "If book name/title/page number are not visible, return null. "
                            "Preserve paragraph breaks with \\n."
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

    # With structured outputs, the model returns valid JSON in output_text
    data = json.loads(resp.output_text)

    out = {
        "book_name": data.get("book_name", None),
        "title": data.get("title", None),
        "page_number": _safe_int(data.get("page_number", None)),
        "text": (data.get("text", "") or ""),
        "source_file": image_path.name,
    }
    return out


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set. Run: export OPENAI_API_KEY='...'")

    if not INBOX_DIR.exists():
        raise FileNotFoundError(f"Missing folder: {INBOX_DIR}")

    client = OpenAI()

    images = [
        p for p in sorted(INBOX_DIR.iterdir())
        if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ]

    if not images:
        print(f"No images found in {INBOX_DIR}")
        return

    for img in images:
        out_path = img.with_suffix(img.suffix + OUT_SUFFIX)  # p98.jpg.json
        if out_path.exists():
            print(f"Skip (already has JSON): {out_path.name}")
            continue

        print(f"Extracting: {img.name}")
        data = extract_one_image(client, img)
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {out_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()
