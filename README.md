books_judge — Minimal, Non-Hallucinatory Book Page Extraction

This repository demonstrates a simple, reliable pipeline for working with photos of book pages using AI without hallucinating metadata.

It intentionally avoids complex agents, judges, or completion logic and instead combines:

deterministic structure (folders, rules)

AI where it works well (OCR + light classification)

What This Repo Contains (Only Two Scripts)
1️⃣ extract_openai.py — Image → JSON

Extracts exact page text from images and saves one JSON per page.

What it does

Reads book page images from a structured folder

Uses OpenAI vision to extract only what is visible

Attaches book + author from folder name (not inference)

Optionally classifies life stage (childhood / adulthood / both / unclear)

Folder structure (important):

inbox_photos/
└── book_name_author_name/
    ├── page_001.jpg
    ├── page_002.jpg


Output (one JSON per image):

{
  "book_name": "...",
  "author_name": "...",
  "page_number": null,
  "text": "Exact extracted text...",
  "life_stage_flag": "childhood | adulthood | both | unclear",
  "source_file": "page_001.jpg",
  "reference": "path/to/page_001.jpg"
}


Rules:

No guessing book titles or authors

Page numbers only if visible

Missing metadata stays missing by design

2️⃣ extract_table.py — JSON → CSV

Collects all extracted JSON files into a readable CSV table.

What it does

Reads all page-level JSONs

Sorts rows by book_name → page_number

Adds text length + preview for review

Outputs a clean CSV for inspection

Output:

extraction_table.csv

Quick Inspection with Pandas

Once the CSV is created, you can explore it immediately:

import pandas as pd

df = pd.read_csv("extraction_table.csv")

# Sort again if needed
df = df.sort_values(["book_name", "page_number"])

# Quick sanity checks
df[["book_name", "author_name"]].drop_duplicates()
df["life_stage_flag"].value_counts()

# Preview text
df[["book_name", "page_number", "text"]].head()


This makes missing metadata, ordering issues, or OCR problems obvious and inspectable.

Why This Approach Works

Key principles behind this design:

Structure beats inference
Folder names are more reliable than asking a model to guess book titles.

Extraction ≠ completion
Most pages do not contain titles or chapter names — filling them in would hallucinate.

Use ML where it’s mature
OCR and coarse classification work well; metadata completion does not.

Simple pipelines are easier to trust
Fewer moving parts → fewer silent errors.

Outcome

The result is a clean, auditable dataset:

page-level text

stable metadata

human-readable table

no hidden assumptions

This dataset is ready for downstream analysis, clustering, or research — without needing to “fix” hallucinated fields later.
