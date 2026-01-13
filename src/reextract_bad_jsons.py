import json, io, base64, os
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image
from openai import OpenAI

INBOX_DIR = Path.home() / "Documents" / "books" / "inbox_photos"
MODEL = "gpt-4o-mini"
client = OpenAI()

def _safe_int(x: Any) -> Optional[int]:
    try:
        return None if x is None else int(x)
    except Exception:
        return None

def image_to_data_url_under_5mb(path: Path, max_bytes: int = 5 * 1024 * 1024) -> str:
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

def extract_one_image(image_path: Path) -> Dict[str, Any]:
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
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": (
                    "Extract the visible page text accurately. "
                    "If book name/title/page number are not visible, return null. "
                    "Preserve paragraph breaks with \\n."
                )},
                {"type": "input_image", "image_url": data_url},
            ],
        }],
        text={"format": {"type": "json_schema", "name": "extract", "strict": True, "schema": schema}},
    )

    data = json.loads(resp.output_text)

    return {
        "book_name": data.get("book_name", None),
        "title": data.get("title", None),
        "page_number": _safe_int(data.get("page_number", None)),
        "text": (data.get("text", "") or ""),
        "source_file": image_path.name,
    }

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set.")

    bad = []
    for jf in sorted(INBOX_DIR.glob("*.json")):
        try:
            json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            bad.append(jf)

    if not bad:
        print("No bad JSON files found.")
        return

    print(f"Bad JSON files: {len(bad)}")

    for jf in bad:
        # determine image filename
        # expected sidecar pattern: image.jpg.json
        image_name = jf.name[:-5]  # strip trailing ".json"
        img_path = INBOX_DIR / image_name

        if not img_path.exists():
            print(f"Skip (missing image): {image_name}")
            continue

        print(f"Re-extracting: {img_path.name}")
        data = extract_one_image(img_path)
        jf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Fixed: {jf.name}")

    print("Done.")

if __name__ == "__main__":
    main()
