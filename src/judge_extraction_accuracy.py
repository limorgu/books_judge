import json
from pathlib import Path
from openai import OpenAI
from PIL import Image
import io, base64

INBOX_DIR = Path.home() / "Documents" / "books" / "inbox_photos"
OUT_JSON = Path.home() / "Documents" / "books" / "judge_results.json"

MODEL = "gpt-4o-mini"

client = OpenAI()

def image_to_data_url(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def judge_one(image_path: Path, data: dict) -> dict:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "text_accuracy": {"type": "integer", "enum": [1, 2, 3]},
            "page_number_accuracy": {
                "anyOf": [{"type": "integer", "enum": [1, 2, 3]}, {"type": "null"}]
            },
            "title_accuracy": {
                "anyOf": [{"type": "integer", "enum": [1, 2, 3]}, {"type": "null"}]
            },
            "notes": {"type": "string"},
        },
        "required": [
            "text_accuracy",
            "page_number_accuracy",
            "title_accuracy",
            "notes",
        ],
    }

    prompt = (
        "You are judging the accuracy of text extracted from a photo of a book page.\n\n"
        "Rate each item on a scale of 1–3:\n"
        "1 = incorrect / major errors\n"
        "2 = mostly correct with minor errors\n"
        "3 = accurate and faithful\n\n"
        "Use null if a field is not visible on the page.\n"
        "Be strict but fair."
    )

    data_url = image_to_data_url(image_path)

    resp = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_text",
                        "text": json.dumps(data, ensure_ascii=False),
                    },
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "judge_result",
                "strict": True,
                "schema": schema,
            }
        },
    )

    # Structured outputs guarantee valid JSON here
    return json.loads(resp.output_text)

def main():
    results = []

    json_files = list(INBOX_DIR.glob("*.json"))[:10]  # 👈 sample first 10
    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        img = INBOX_DIR / data["source_file"]

        print(f"Judging {img.name}")
        scores = judge_one(img, data)

        results.append({
            "file": img.name,
            **scores
        })

    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved judge results to {OUT_JSON}")

if __name__ == "__main__":
    main()
