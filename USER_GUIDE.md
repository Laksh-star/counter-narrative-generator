# User Guide

This guide explains how to run the Counter-Narrative Generator end-to-end and what to expect from its outputs.

![Panchatantra Three-Fish Framework](images/three-fish-framework.png)

## Who This Is For

- You want a fast way to challenge conventional business wisdom using Lenny's Podcast transcripts.
- You are comfortable running a Python CLI and editing a `.env` file.

## Prerequisites

- Python 3.10+ recommended
- An OpenRouter API key

## First Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key
cp .env.example .env
# Edit .env and set: OPENROUTER_API_KEY=sk-or-v1-your-key

# 3. Load transcript data into ChromaDB
python main.py load
```

Expected: a `chroma_db/` folder appears and `python main.py stats` shows ~15,969 chunks.

## Ask a Question

```bash
python main.py query "You need product-market fit before scaling"
```

This returns:
- Contrarian guests and their reasoning
- A balanced synthesis describing when each perspective applies

## Output Files

By default, results are printed to the terminal. You can also save full JSON:

```bash
python main.py query "belief" -o outputs/my_result.json
```

The output JSON includes:
- `forethought`: contrarian findings
- `quickaction`: structured arguments
- `examiner`: synthesis and meta-lesson

## Interactive Mode

```bash
python main.py interactive
```

Use this to explore multiple queries without restarting the CLI.

## Evaluation (Optional)

Sample test queries live in `evaluation/test_queries.json`. You can iterate through them manually or use them to sanity-check changes to prompts or models.

## Troubleshooting

- `OPENROUTER_API_KEY` missing: edit `.env` and set the key, then re-run.
- Empty or weak results: try a more specific belief, or re-run `python main.py load --force`.
- Slow queries or high cost: swap to cheaper models in `.env` (see README configuration section).
- Chroma errors: delete `chroma_db/` and run `python main.py load` again.

## Notes on Data

Transcript data is pre-processed and stored under `content/output/`. Loading builds the vector store from `content/output/chunks.jsonl`.
