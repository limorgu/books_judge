books_judge
Book-page extraction pipeline + evaluation (working)
Next goal: content-based book attribution
This repository documents an end-to-end pipeline for extracting structured text from photographed book pages and organizing it into analyzable data.
The pipeline is working and stable for:
text extraction
page-level metadata capture
JSON generation
table aggregation
basic evaluation
The open problem (Step B) is book/author attribution at scale when metadata is not printed on interior pages.

What works (current state)
✔ Step 1 — Page-level extraction (WORKING)
We built a reliable extraction pipeline using OpenAI Vision + structured outputs.
Input
Photos of book pages (phone scans)
Stored locally (not committed)
Output
One JSON per image (image.jpg.json)
Fields:
text (full page text, paragraph-preserved)
page_number (if visible)
book_name (if explicitly printed)
author (if explicitly printed)
source_file
Key design decision
The extractor is conservative.
It does not guess book name or author if they are not visible on the page.
Script
src/extract_openai.py

Behavior
Reads images from:
~/Documents/books/inbox_photos
Skips images that already have a .json sidecar
Automatically resizes/compresses images under upload limits
Produces structured JSON using OpenAI’s json_schema output
Run
source ~/Documents/books/my311/bin/activate
export OPENAI_API_KEY="YOUR_KEY"
python ~/Documents/books/books_judge/src/extract_openai.py


✔ Step 2 — Aggregation into a table (WORKING)
All extracted page JSONs can be merged into a single review table for inspection.
Script
src/make_extraction_table.py

Output
~/Documents/books/extraction_table.csv

Columns
filename
page_number
book_name
author
text_length
text_preview
This makes it easy to:
scan coverage
spot OCR issues
identify missing metadata
Run
python ~/Documents/books/books_judge/src/make_extraction_table.py
open ~/Documents/books/extraction_table.csv


✔ Step 3 — Quality checks & evaluation (WORKING)
We added lightweight “LLM-as-judge” checks to understand extraction quality and missing fields.
Implemented checks
Invalid / broken JSON detection
Missing field audit
Visibility judgment (is metadata actually visible on the page?)
These steps confirmed that most missing book_name / author fields are expected, not extraction failures.
Interior book pages usually do not repeat title or author.

⚠ Step B — Open problem (NOT SOLVED YET)
The real challenge
After aggregation, the table still contains:
inconsistent book_name values
confusion between:
book title
chapter title
author name
many null book/author entries (by design)
This is not an OCR problem.
It is a content attribution problem.
