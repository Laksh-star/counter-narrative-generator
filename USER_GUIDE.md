# User Guide

This guide explains how to use the Counter-Narrative Generator to challenge conventional business wisdom using Lenny's Podcast transcripts.

![Panchatantra Three-Fish Framework](images/three-fish-framework.png)

## Who This Is For

- You want to challenge conventional business wisdom using Lenny's Podcast transcripts
- You want to understand when popular advice applies (and when it doesn't)
- You're looking for productive disagreement, not just confirmation

## Two Ways to Use This Tool

### 🌐 Option 1: Web Application (Recommended)

The easiest way to use the Counter-Narrative Generator is through the web interface.

#### Prerequisites
- Docker and Docker Compose
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

#### Quick Start

1. **Clone and setup**
   ```bash
   git clone https://github.com/Laksh-star/counter-narrative-generator.git
   cd counter-narrative-generator
   cp .env.example .env
   ```

2. **Configure API key**
   Edit `.env` and add:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-key
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Open your browser**
   - Frontend: http://localhost:3000
   - Backend API docs: http://localhost:8000/docs

#### Using the Web Interface

1. **Enter your belief** - Type a piece of conventional wisdom you want to challenge
   - Example: "You need product-market fit before scaling"
   
2. **Select topics (optional)** - Filter results by specific areas like "growth-strategy" or "product-market-fit"

3. **Set number of perspectives** - Choose how many contrarian views to find (1-10)

4. **Add your context (optional)** - Describe your situation for personalized guidance
   - Example: "I'm a B2B SaaS founder with 100 users"

5. **Submit** - Watch real-time progress as the three agents work:
   - **Forethought**: Searching for contrarian perspectives...
   - **Quickaction**: Structuring arguments...
   - **Examiner**: Synthesizing insights...

6. **Review results** - See:
   - **Contrarian Perspectives**: Guests who disagree, with quotes and citations
   - **Structured Arguments**: Key reasoning and evidence
   - **Synthesis**: When each perspective applies, decision framework, meta-lessons

#### Debug Mode

Add `?debug=1` to the URL to see detailed internal data:
```
http://localhost:3000?debug=1
```

### 💻 Option 2: Command Line (Advanced)

For programmatic access or integration into scripts.

#### Prerequisites
- Python 3.10+
- OpenRouter API key

#### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and set: OPENROUTER_API_KEY=sk-or-v1-your-key

# 3. Load transcript data into ChromaDB (one-time setup, ~6 minutes)
python main.py load
```

Expected: a `chroma_db/` folder appears and `python main.py stats` shows ~15,969 chunks.

#### Basic Usage

```bash
# Ask a question
python main.py query "You need product-market fit before scaling"

# Filter by topics
python main.py query "Move fast and break things" --topics growth-strategy engineering

# Add user context
python main.py query "Focus on one thing" --user-context "B2B SaaS startup, 50 customers"

# Save to file
python main.py query "VC funding is essential" -o outputs/result.json

# View stats
python main.py stats
```

#### Interactive Mode

```bash
python main.py interactive
```

Use this to explore multiple queries without restarting.

## Understanding the Output

### 1. Contrarian Perspectives (Forethought Agent)

The Scout finds guests who disagree with your belief:

```
🔍 CONTRARIAN PERSPECTIVES FOUND

Patrick Campbell
Episode: #271 | Citation: 00:42:15-00:43:30
Position: Many businesses achieve scale generating tens of millions 
in cash flow without any VC funding
Quote: "The question isn't should I raise, it's what game am I playing..."
Relevance Score: 8/10
```

### 2. Structured Arguments (Quickaction Agent)

The Miner extracts the reasoning:

```
📊 STRUCTURED ARGUMENTS

Thesis: VC funding creates perverse incentives before achieving sustainable unit economics

Reasoning:
• Forces premature scaling to justify valuation
• Dilutes founder control over strategic decisions
• Creates pressure for exit timing misaligned with product readiness

Evidence:
• Example: Mailchimp scaled to $700M revenue profitably without VC
• Data: 94% of companies that reach $100M+ ARR are profitable (not VC-backed)
```

### 3. Synthesis (Examiner Agent)

The Judge provides context and boundaries:

```
⚖️ SYNTHESIS & DECISION FRAMEWORK

Real Disagreement: Speed-at-all-costs vs. Sustainable Control

✅ VC funding applies when:
   • Winner-take-all market with strong network effects
   • First-mover advantage is critical
   • Capital enables defensible moat (e.g., data, brand)

❌ Bootstrap applies when:
   • Competitive advantage is deep domain expertise
   • Profitability achievable in 12-24 months
   • Market rewards quality over speed

💡 META-LESSON:
The question isn't "Should I raise?" but "What game am I playing?"
Don't adopt VC metrics if you aren't playing a VC game.
```

## Tips for Better Results

### Craft Good Queries

**Good:**
- "You need product-market fit before scaling"
- "Move fast and break things"
- "Focus on one thing and do it really well"

**Less Effective:**
- Too vague: "How do I grow?"
- Too specific: "Should I use Redis or Memcached?"
- Not a belief: "What did Brian Chesky say about growth?"

### Use Topic Filters

Available topics:
- `product-market-fit`
- `growth-strategy`
- `pricing`
- `hiring`
- `fundraising`
- `leadership`
- `user-research`
- `experimentation`
- `positioning`
- `roadmap`
- `culture`
- `product-development`

### Add Context

Including your situation helps the Examiner provide personalized guidance:
```
User Context: "Seed-stage B2B SaaS, $50K MRR, 
deciding between product expansion vs. going deeper on core feature"
```

## Output Files (CLI Mode)

Save results for later review:

```bash
# JSON format
python main.py query "belief" -o outputs/my_result.json

# The output includes:
{
  "conventional_wisdom": "Your belief",
  "forethought": { "contrarian_findings": [...] },
  "quickaction": { "structured_arguments": [...] },
  "examiner": { "synthesis": "...", "decision_framework": {...} },
  "metadata": { "total_tokens": 12453, "execution_time_ms": 45231 }
}
```

## Troubleshooting

### Web App Issues

**Backend won't start**
```bash
# Check API key
docker-compose logs backend | grep "OPENROUTER_API_KEY"

# Rebuild
docker-compose down -v
docker-compose up --build
```

**Frontend can't connect to backend**
- Ensure backend is running: `curl http://localhost:8000/api/health`
- Check browser console for WebSocket errors

**No contrarian perspectives found**
- Try a different belief (more specific or more controversial)
- Check backend logs: `docker-compose logs backend`
- Verify vector store loaded: check backend startup logs for "15,969 chunks"

### CLI Issues

**OPENROUTER_API_KEY missing**
- Edit `.env` and set the key
- Verify: `echo $OPENROUTER_API_KEY` (after `source .env`)

**Empty or weak results**
- Try a more specific belief
- Force reload: `python main.py load --force`

**Slow queries or high cost**
- Use cheaper models in `.env`:
  ```
  FORETHOUGHT_MODEL=google/gemini-2.5-flash-lite
  QUICKACTION_MODEL=google/gemini-2.5-flash-lite
  ```

**ChromaDB errors**
```bash
# Delete and reload
rm -rf chroma_db/
python main.py load
```

## Data & Privacy

### What Data Is Used?

- **Source**: ~300 episodes of Lenny's Podcast (public transcripts)
- **Processing**: Split into 15,969 semantic chunks
- **Storage**: Local ChromaDB vector database
- **No tracking**: Your queries are not logged or stored

### How It Works

1. **Embedding**: Chunks are embedded using OpenAI's text-embedding-3-small
2. **Search**: Your query is matched against chunks using cosine similarity
3. **Contrarian detection**: Chunks with disagreement signals are prioritized
4. **Analysis**: Three AI agents process results using OpenRouter models

## Advanced Configuration

### Model Selection (Cost vs. Quality)

Edit `.env` to customize:

```bash
# Budget option (~$0.01/query)
FORETHOUGHT_MODEL=google/gemini-2.5-flash-lite
QUICKACTION_MODEL=google/gemini-2.5-flash-lite
EXAMINER_MODEL=google/gemini-2.5-flash

# Balanced (default, ~$0.03/query)
FORETHOUGHT_MODEL=google/gemini-2.5-flash
QUICKACTION_MODEL=google/gemini-2.5-flash-lite
EXAMINER_MODEL=anthropic/claude-sonnet-4.5

# Premium (~$0.08/query)
FORETHOUGHT_MODEL=anthropic/claude-sonnet-4.5
QUICKACTION_MODEL=anthropic/claude-sonnet-4.5
EXAMINER_MODEL=anthropic/claude-opus-4.5
```

### API Integration

Use the REST API directly:

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "belief": "You need product-market fit before scaling",
    "topics": ["growth-strategy"],
    "n_results": 5,
    "verbose": true
  }'
```

## Evaluation & Testing

Sample test queries are in `evaluation/test_queries.json`. Use them to:
- Sanity-check changes to prompts or models
- Compare output quality across model configurations
- Benchmark cost and performance

## Next Steps

- Deploy to Google Cloud Run: See [DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Explore the API: Visit http://localhost:8000/docs
- Customize agents: Edit prompt templates in `backend/src/agents/`
- Add your own data: See `backend/src/data/prepare_chunks.py`

## Getting Help

- **Issues**: https://github.com/Laksh-star/counter-narrative-generator/issues
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **API Documentation**: http://localhost:8000/docs (when running)

---

**Remember**: This tool provides perspectives, not answers. Use it to expand your thinking, not replace your judgment.
