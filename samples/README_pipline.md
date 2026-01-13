# books_judge — book-page extraction + judge eval

This repo contains a small pipeline to:
1) extract structured text from photos of book pages into JSON files, and  
2) run a lightweight “LLM-as-judge” eval to spot-check extraction accuracy.

It was built originally while experimenting with MCP servers (filesystem), but the working production path here uses the OpenAI API directly (simpler + stable).

---

## Folder layout

Recommended structure:

books_judge/
src/
extract_pages_openai.py
judge_extraction_accuracy.py
make_extraction_table.py
samples/
(a few example *.json outputs)
.gitignore
README.md

yaml
Copy code

Raw images should **not** be committed (see `.gitignore`).

---

## Local “inbox” folder (data lives outside the repo)

We keep images in a local folder (not committed):

~/Documents/books/inbox_photos

vbnet
Copy code

You can drop new page photos here anytime.

The extractor writes sidecar JSON files next to each image:

p98.jpg
p98.jpg.json

yaml
Copy code

---

## Setup

### 1) Create and activate a virtualenv (example)
```bash
cd ~/Documents/books
/opt/homebrew/bin/python3.11 -m venv my311
source my311/bin/activate
python -m pip install --upgrade pip
2) Install dependencies
bash
Copy code
python -m pip install openai pillow
3) Set API key
bash
Copy code
export OPENAI_API_KEY="YOUR_KEY"
(Optional: put it in your shell profile or a local .env — never commit secrets.)

Extraction: image -> JSON dictionary
Script: src/extract_pages_openai.py

What it does:

reads all images in ~/Documents/books/inbox_photos

for each image, creates a JSON dictionary with keys:

book_name, title, page_number, text, source_file

skips already processed images (if image.jpg.json exists)

automatically compresses/resizes images to stay under upload limits


## Setup

### 1) Create and activate a virtualenv (example)
```bash
cd ~/Documents/books
/opt/homebrew/bin/python3.11 -m venv my311
source my311/bin/activate
python -m pip install --upgrade pip

2) Install dependencies
python -m pip install openai pillow

3) Set API key
export OPENAI_API_KEY="YOUR_KEY"

Extraction: image -> JSON dictionary

Script: src/extract_pages_openai.py

What it does:

reads all images in ~/Documents/books/inbox_photos

for each image, creates a JSON dictionary with keys:

book_name, title, page_number, text, source_file

skips already processed images (if image.jpg.json exists)

automatically compresses/resizes images to stay under upload limits

Run:

source ~/Documents/books/my311/bin/activate
export OPENAI_API_KEY="YOUR_KEY"
python ~/Documents/books/books_judge/src/extract_pages_openai.py


Only new pages:

This happens automatically because the script checks:

if image.jpg.json exists → skip

To re-run a specific image:

delete its json sidecar and run again:

rm ~/Documents/books/inbox_photos/<image>.jpg.json

Build a review table (CSV)

Script: src/make_extraction_table.py

Creates a CSV table from all sidecar JSONs (good for spot-checking):

filename

page_number

title

text length

preview

Run:

python ~/Documents/books/books_judge/src/make_extraction_table.py
open ~/Documents/books/extraction_table.csv

Judge eval (quick accuracy check)

Script: src/judge_extraction_accuracy.py

What it does:

samples a small set of extracted pages

sends the image + extracted JSON back to the model

returns scores (1–3) for:

text accuracy

page number accuracy

title accuracy

saves results to ~/Documents/books/judge_results.json

Run:

python ~/Documents/books/books_judge/src/judge_extraction_accuracy.py


Interpretation:

3 = accurate

2 = mostly correct (minor OCR issues)