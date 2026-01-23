# Counter-Narrative Generator

**Mine contrarian wisdom from Lenny's Podcast using the Panchatantra Three-Fish Framework**

Given any conventional business wisdom, this tool finds podcast guests who disagree, extracts their reasoning, and synthesizes a balanced debate to help you think more clearly about when each perspective applies.

![Panchatantra Three-Fish Framework](images/three-fish-framework.png)

## The Panchatantra Three-Fish Framework

Inspired by the ancient Indian tale of three fish with different survival strategies, this system uses three specialized AI agents:

| Agent | Role | Model |
|-------|------|-------|
| **Forethought** (Anagatavidhata) | The Contrarian Scout - searches for guests who challenge conventional wisdom | Gemini 2.5 Flash |
| **Quickaction** (Pratyutpannamati) | The Argument Miner - structures arguments with evidence and conditions | Gemini 2.5 Flash Lite |
| **Examiner** (Yadbhavishya) | The Debate Architect - synthesizes balanced guidance and meta-lessons | Claude Sonnet 4.5 |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your OpenRouter API key
cp .env.example .env
# Edit .env and add: OPENROUTER_API_KEY=sk-or-v1-your-key

# 3. Load the podcast transcripts into ChromaDB
python main.py load

# 4. Challenge a conventional wisdom
python main.py query "You need product-market fit before scaling"

# Or use interactive mode
python main.py interactive
```

## Example Output

**Query:** *"Hiring fast is the key to startup success"*

**Contrarian findings:**

> **Edwin Chen**: "The standard playbook is to blitz scale by hiring as fast as possible. And I've always disagreed."

> **Ben Horowitz**: "Build that team slowly and deliberately, paced to your ability to integrate and then manage them."

**Meta-lesson:** The effectiveness of hiring speed depends on your stage, the role complexity, and your capacity to integrate new people.

## CLI Commands

```bash
python main.py load              # Load 15,969 chunks into ChromaDB
python main.py load --force      # Force reload
python main.py stats             # Show vector store statistics
python main.py query "belief"    # Challenge a conventional wisdom
python main.py query "belief" -v # Verbose mode (see agent progress)
python main.py query "belief" -s # Auto-save results to outputs/
python main.py query "belief" -o result.json  # Save to specific file
python main.py search "keyword"  # Direct vector search (debugging)
python main.py interactive       # Interactive exploration mode
```

## Sample Queries to Try

```
"You should always build what users ask for"
"Data-driven decisions are always better than intuition"
"You need to raise VC money to build a successful company"
"Move fast and break things"
"Every team needs a single North Star metric"
"The customer is always right"
```

## Project Structure

```
├── main.py                      # CLI entry point
├── src/
│   ├── config.py               # Model config, topic taxonomy
│   ├── workflow.py             # Three-Fish orchestration
│   ├── agents/
│   │   ├── base.py             # Base agent with OpenRouter
│   │   ├── forethought.py      # Contrarian Scout
│   │   ├── quickaction.py      # Argument Miner
│   │   └── examiner.py         # Debate Architect
│   └── data/
│       ├── prepare_chunks.py   # Chunk enrichment
│       └── vectorstore.py      # ChromaDB integration
├── scripts/
│   └── ingest_transcripts.py  # Transcript .txt → chunks.jsonl pipeline
├── content/output/             # Podcast transcript data
│   ├── chunks.jsonl            # 15,969 searchable chunks
│   ├── episodes_index.jsonl   # Episode metadata index
│   ├── manifest.csv           # Episode-level stats
│   └── stats.json              # Dataset statistics
├── outputs/                    # Saved query results (created on --save)
└── chroma_db/                  # Vector store (created on load)
```

## Data

The repository includes processed transcripts from **299 episodes** of Lenny's Podcast:
- 57,582 conversation turns
- 15,969 searchable chunks (~280 words each)
- Guests include: Bob Moesta, Brian Chesky, Marty Cagan, Shreyas Doshi, and many more

### Regenerating chunks from raw transcripts

If you want to re-process the transcripts (e.g., with different chunk sizes), use the ingestion script:

```bash
python scripts/ingest_transcripts.py \
  --input_dir /path/to/transcript-txt-files \
  --output_dir content/output \
  --target_words 280 \
  --overlap_turns 1
```

Options:
- `--target_words` — approximate words per chunk (default: 280)
- `--overlap_turns` — turn overlap between consecutive chunks (default: 1)
- `--include_intro` — include intro/preamble turns in chunks
- `--redact_pii` — replace detected emails/phone numbers with redaction tokens

The script requires no external dependencies (standard library only) and produces:
- `chunks.jsonl` — flat file for RAG ingestion
- `episodes_index.jsonl` — episode metadata
- `manifest.csv` — per-episode stats
- `episodes/` — individual episode JSONs with full turn data

## How It Works

1. **Vector Search**: Your query is embedded and searched against 15,969 podcast chunks using ChromaDB
2. **Contrarian Boosting**: Chunks with disagreement signals ("I disagree", "contrary to popular belief", etc.) are prioritized
3. **Three-Fish Pipeline**:
   - Forethought finds 3-5 guests with contrarian views
   - Quickaction structures their arguments (thesis, reasoning, evidence, conditions)
   - Examiner synthesizes when each view applies and extracts meta-lessons

## Cost

Using OpenRouter with cost-optimized models:
- **~$0.02-0.05 per query**
- Forethought + Quickaction: ~$0.005 (Gemini Flash)
- Examiner: ~$0.02-0.04 (Claude Sonnet 4.5)

## Configuration

Override models via environment variables:

```bash
OPENROUTER_API_KEY=sk-or-v1-...    # Required
FORETHOUGHT_MODEL=google/gemini-2.5-flash
QUICKACTION_MODEL=google/gemini-2.5-flash-lite
EXAMINER_MODEL=anthropic/claude-sonnet-4.5
```

## Background

This project combines:
- **Panchatantra wisdom** - The tale of three fish teaches that different strategies (foresight, quick action, acceptance) suit different situations
- **Agentic AI workflows** - Inspired by Andrew Ng's patterns for chaining specialized agents
- **Contrarian thinking** - The best decisions come from understanding both sides of a debate

Read more: [From the Terminator to Workflows: OpenAI Agent Builder's Promise](https://blog.stackademic.com/from-the-terminator-to-workflows-openai-agent-builders-promise-and-the-skeptics-at-the-gate-6d1e43ecf649)

## License

MIT
