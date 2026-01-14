books_judge
A conservative, auditable pipeline for extracting book pages with AI (without hallucination)

This repository demonstrates a methodical, non-hallucinatory workflow for extracting text and minimal metadata from scanned book pages using large language models.

The focus is not on “making AI smart,” but on designing the system so it cannot guess.

Design principles

This pipeline follows four explicit principles:

Ground truth precedes inference
Stable metadata (book name, author name) comes from the file system, not from the model.

Absence of evidence is preserved
If a field is not visible on the page, it is returned as null.

Separation of extraction and interpretation
Text extraction happens before any semantic tagging.

Every output is traceable
Every JSON record references the exact image file that produced it.

Folder structure (authoritative metadata)

Input images live outside the repo, organized by known metadata:

~/Documents/books/inbox_photos/
└── data/
    ├── <book_name>_<author_name>/
    │   ├── page_001.jpg
    │   ├── page_002.jpg
    └── <book_name>_<author_name>/
        ├── page_001.jpg
        ├── page_002.jpg


Important:
book_name and author_name are treated as external facts.
The model is never asked to infer them from page content.

Step 1 — Page-level extraction (image → JSON)

Script: src/extract_openai.py

Each image is processed independently using OpenAI Vision with strict structured output.

A JSON “sidecar” file is written next to each image.

Output schema (per page)
{
  "book_name": "<book_name>",
  "author_name": "<author_name>",
  "page_number": 143,
  "text": "Exact page text with paragraph breaks",
  "life_stage_flag": "childhood | adulthood | both | unclear",
  "source_file": "page_143.jpg",
  "reference": "data/<book_name>_<author_name>/page_143.jpg"
}

Extraction rules

Text is extracted verbatim (no summarization)

Page number is returned only if visibly printed

Book and author names come from folder structure

Missing information stays null

Output must conform to a JSON schema (no free-form text)

This prevents the model from “helpfully” filling gaps.

Step 2 — Minimal semantic tagging (bounded inference)

Each page receives one constrained semantic label:

"life_stage_flag": "childhood | adulthood | both | unclear"


This reflects whether the page content refers primarily to childhood experiences, adulthood experiences, both, or cannot be determined.

No psychological interpretation or causal explanation is attempted.

Step 3 — Build an extraction review table (JSON → CSV)

Script: src/make_extraction_table.py

This step converts all extracted JSON files into a single, human-readable table for review.

What the table is for

Checking coverage across books

Spotting missing page numbers

Verifying text quality

Confirming correct ordering

What the script does

Recursively reads all JSON sidecars

Extracts key fields:

book_name

author_name

page_number

text length

short text preview

Sorts rows by:

book_name

page_number

source_file

Writes a CSV file

Output
~/Documents/books/extraction_table.csv

Core logic (simplified)
rows.sort(
    key=lambda r: (
        r["book_name"] or "",
        r["page_number"] if isinstance(r["page_number"], int) else 10**9,
        r["source_file"] or ""
    )
)


This guarantees stable, interpretable ordering even when page numbers are missing.

Why this table matters

The table makes failures visible.

Instead of trusting the model, you can see:

where metadata is missing

where OCR quality degrades

where page order breaks

where semantic flags feel wrong

This is a deliberate anti-hallucination design choice.

What this pipeline does not do

Intentionally avoided:

Guessing book or author names

Inferring missing page numbers

Merging or “cleaning” text

Drawing psychological conclusions

Auto-correcting uncertainty

These behaviors are where most LLM hallucinations originate.

Open problem (next step)

One unresolved challenge remains:

How to complete or cluster metadata when it is not visible on the page.

Possible future directions:

Content-based clustering constrained by known book folders

Probabilistic attribution with explicit uncertainty

Human-in-the-loop confirmation

This is left open by design.