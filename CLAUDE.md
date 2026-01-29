# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains two components:

1. **Data**: Processed podcast transcript data from Lenny's Podcast (299 episodes, 15,969 chunks)
2. **Counter-Narrative Generator**: A Panchatantra Three-Fish AI workflow for mining contrarian wisdom

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Load data into ChromaDB
python main.py load

# Run a query
python main.py query "You need product-market fit before scaling"

# Interactive mode
python main.py interactive
```

## Project Structure

```
├── main.py                      # CLI entry point
├── src/
│   ├── config.py               # Configuration and model settings
│   ├── workflow.py             # Three-Fish workflow orchestration
│   ├── agents/
│   │   ├── base.py             # Base agent class
│   │   ├── forethought.py      # Contrarian Scout agent
│   │   ├── quickaction.py      # Argument Miner agent
│   │   └── examiner.py         # Debate Architect agent
│   └── data/
│       ├── prepare_chunks.py   # Chunk enrichment utilities
│       └── vectorstore.py      # ChromaDB vector store
├── content/output/             # Podcast transcript data
│   ├── chunks.jsonl            # Main data file for RAG
│   ├── episodes/               # Individual episode JSONs
│   └── stats.json              # Dataset statistics
├── evaluation/
│   └── test_queries.json       # Test cases for evaluation
└── chroma_db/                  # ChromaDB persistence (created on load)
```

## Architecture: Panchatantra Three-Fish Framework

The workflow uses three agents inspired by the Panchatantra tale:

| Agent | Model | Role | Cost |
|-------|-------|------|------|
| **Forethought** | `google/gemini-2.5-flash` | Searches for contrarian perspectives | ~$0.15/1M |
| **Quickaction** | `google/gemini-2.5-flash-lite` | Structures arguments | ~$0.10/1M |
| **Examiner** | `anthropic/claude-sonnet-4` | Synthesizes balanced debate | ~$3/1M |

Flow: `User Query → Forethought (RAG search) → Quickaction (structure) → Examiner (synthesis)`

## CLI Commands

```bash
python main.py load              # Load chunks into ChromaDB
python main.py load --force      # Force reload
python main.py stats             # Show vector store statistics
python main.py query "belief"    # Challenge a conventional wisdom
python main.py query "belief" -v # Verbose mode
python main.py query "belief" -o result.json  # Save full output
python main.py search "keyword"  # Direct vector search (debugging)
python main.py interactive       # Interactive exploration mode
```

## Data Schemas

### Chunk (in ChromaDB)
```python
{
    "episode_id": "guest-slug",
    "guest": "Guest Name",
    "speaker_primary": "Guest Name",
    "t_start": 465,
    "t_end": 521,
    "citation": "Guest Name (7:45)",
    "has_contrarian_signal": True,
    "contrarian_signals": "i disagree,the problem with that",
    "topics": "product-market-fit,growth-strategy",
    "text": "..."
}
```

### Workflow Output
```python
{
    "conventional_wisdom": "...",
    "forethought": { "contrarian_findings": [...] },
    "quickaction": { "structured_arguments": [...] },
    "examiner": {
        "title": "...",
        "contrarian_views": [...],
        "synthesis": {
            "real_disagreement": "...",
            "conventional_wisdom_applies_when": [...],
            "contrarian_view_applies_when": [...],
            "meta_lesson": "..."
        }
    }
}
```

## Configuration

Models can be overridden via environment variables:

```bash
OPENROUTER_API_KEY=sk-or-v1-...    # Required
FORETHOUGHT_MODEL=google/gemini-2.5-flash
QUICKACTION_MODEL=google/gemini-2.5-flash-lite
EXAMINER_MODEL=anthropic/claude-sonnet-4
EMBEDDING_MODEL=openai/text-embedding-3-small
```

## Key Files to Understand

- [src/workflow.py](src/workflow.py) - Main orchestration logic
- [src/agents/examiner.py](src/agents/examiner.py) - Final synthesis agent
- [src/data/vectorstore.py](src/data/vectorstore.py) - ChromaDB integration
- [src/config.py](src/config.py) - Model and topic configuration

## Example Query Output

```
🎯 COUNTER-NARRATIVE REPORT
   Challenging the PMF-First Orthodoxy

📌 CONVENTIONAL WISDOM:
   "You need product-market fit before scaling"

🔴 CONTRARIAN PERSPECTIVES:

   ▸ Brian Chesky
     Thesis: Sometimes you need to scale into PMF, not wait for it
     Key Insight: Market conditions can force your hand
     [brian-chesky | 15:23]

⚖️ SYNTHESIS:
   Real Disagreement: Context - when markets are winner-take-all vs. not

   ✅ Conventional wisdom applies when:
      • Market is stable and competitive
      • You have runway to iterate

   ❌ Contrarian view applies when:
      • Network effects create winner-take-all dynamics
      • Speed of market capture matters more than efficiency

   💡 META-LESSON:
      PMF is a spectrum, not a binary. The question is how much fit
      you need given your market dynamics.
```
