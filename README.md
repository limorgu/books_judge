books_judge

A simple, reliable pipeline for extracting book text from images — without hallucinating metadata

This repository documents a minimal, human-controlled workflow for turning photographed book pages into structured data (JSON + CSV), while avoiding common AI failure modes such as invented book titles, authors, or chapters.

The design principle is simple:

Let AI do what it’s good at (reading text),
and let humans control structure and meaning.

What this repository does

Using two small Python scripts, you can:

Extract exact text from book page photos

One JSON file per page

Includes book name, author name, page number (if visible), and full text

Combine all JSON files into a readable CSV table

Ordered by book name → page number

Easy to review, sort, and analyze with Excel, Numbers, or pandas

No databases.
No agents.
No MCP.
No guessing.

Folder structure (important)

Your photos are stored methodically, not randomly.

inbox_photos/
└── Book_Name_Author_Name/
    ├── IMG_001.jpg
    ├── IMG_002.jpg
    └── IMG_003.jpg


Example:

inbox_photos/
└── Its_Just_Your_Imagination_Revital_Shiri_Horowitz/


This structure is intentional:

Book name and author are taken from the folder

The model is never asked to guess them

This alone eliminates a major source of hallucination

Step 0 — One-time setup (no coding knowledge required)
1. Install Python

Make sure Python 3.10+ is installed:

python --version


If not, download from: https://www.python.org

2. Create a virtual environment (recommended)

From the project folder:

python -m venv venv
source venv/bin/activate   # macOS / Linux


You should now see (venv) in your terminal.

3. Install dependencies
pip install openai pillow pandas

4. Set your OpenAI API key (once)
macOS / Linux (recommended)
export OPENAI_API_KEY="your-key-here"


To make this permanent, add it to ~/.zshrc or ~/.bashrc.

The key is not stored in code or in this repository.

Step 1 — Extract text from images
Script

extract_openai.py

What it does

Walks through all subfolders under inbox_photos/

Reads each image

Extracts only what is visible

Writes a .json file next to each image

Fields written per page
{
  "book_name": "...",
  "author": "...",
  "page_number": 42,
  "text": "... exact page text ...",
  "life_stage_flag": "childhood | adulthood | both | unclear",
  "source_file": "IMG_001.jpg",
  "reference": "full/path/to/image"
}

Run it
python extract_openai.py


Re-running the script is safe:

Images with existing .json files are skipped automatically

Step 2 — Build a review table (CSV)
Script

extract_table.py

What it does

Reads all JSON files recursively

Combines them into a single CSV

Sorts by:

book_name

page_number

Creates short text previews for inspection

Run it
python extract_table.py

Output
extraction_table.csv


You can open this file with:

Excel

Numbers

Google Sheets

pandas

Optional — Inspect with pandas
import pandas as pd

df = pd.read_csv("extraction_table.csv")
df.sort_values(["book_name", "page_number"]).head()


This is useful for:

spotting missing page numbers

checking text quality

preparing downstream analysis

Why this works (and avoids hallucination)

Key design decisions:

Metadata is not inferred

Book name and author come from folders, not the model

Visibility is respected

If a page number isn’t printed, it stays null

No “completion judge”

Pages do not usually contain titles or authors

Asking a model to fill them invites hallucination

Simple rules > clever agents

No MCP, no orchestration, no guesswork

If metadata is missing because it is not present on the page, the correct solution is propagation rules you control, not model guessing.

What this enables next

Chapter-level grouping (by propagating last seen heading)

Thematic labeling

Embeddings / search

Quantitative narrative analysis

Careful, auditable AI-assisted reading

All on clean, human-verifiable data.

Repository philosophy

This project favors:

clarity over cleverness

human control over autonomy

reproducibility over novelty

If you are working with sensitive texts, memoirs, or research material, this approach keeps you in charge.

License / usage

Use freely.
Adapt carefully.
Do not trust models with facts you can structure yourself.
