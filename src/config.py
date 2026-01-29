"""
Configuration for Counter-Narrative Generator
Model selection optimized for cost-effectiveness via OpenRouter
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelConfig:
    """Model configuration with OpenRouter model IDs"""

    # OpenRouter API settings
    api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    base_url: str = "https://openrouter.ai/api/v1"

    # Agent models - optimized for cost/performance
    # Forethought: Fast reasoning for search & discovery
    forethought_model: str = os.getenv(
        "FORETHOUGHT_MODEL",
        "google/gemini-2.5-flash"  # $0.15/$0.60 per 1M - fast, cheap, good reasoning
    )

    # Quickaction: Structured extraction
    quickaction_model: str = os.getenv(
        "QUICKACTION_MODEL",
        "google/gemini-2.5-flash-lite"  # $0.10/$0.40 per 1M - very cheap for extraction
    )

    # Examiner: Best reasoning for synthesis
    examiner_model: str = os.getenv(
        "EXAMINER_MODEL",
        "anthropic/claude-sonnet-4.5"  # Best reasoning/synthesis
    )

    # Embedding model
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "openai/text-embedding-3-small"  # $0.02 per 1M - good quality, cheap
    )

    # Embedding dimension for text-embedding-3-small
    embedding_dimension: int = 1536


@dataclass
class ChromaConfig:
    """ChromaDB configuration"""

    collection_name: str = "lenny_podcast_chunks"
    persist_directory: str = "./chroma_db"


@dataclass
class AppConfig:
    """Main application configuration"""

    models: ModelConfig = None
    chroma: ChromaConfig = None

    # Data paths
    chunks_path: str = "content/output/chunks.jsonl"
    episodes_dir: str = "content/output/episodes"

    # Search settings
    max_contrarian_results: int = 10
    min_relevance_score: float = 0.3

    def __post_init__(self):
        if self.models is None:
            self.models = ModelConfig()
        if self.chroma is None:
            self.chroma = ChromaConfig()


# Global config instance
config = AppConfig()


# Contrarian signal phrases to detect in chunks
CONTRARIAN_SIGNALS = [
    "i disagree",
    "but actually",
    "the opposite is true",
    "that's a misconception",
    "people get this wrong",
    "contrary to popular belief",
    "i'd push back on",
    "the problem with that is",
    "that's not quite right",
    "i think people overestimate",
    "i think people underestimate",
    "the counterintuitive thing",
    "what most people miss",
    "the uncomfortable truth",
    "here's where i differ",
    "i would challenge",
    "the conventional wisdom is wrong",
    "most advice says",
    "everyone tells you to",
    "the standard approach",
    "i've seen the opposite",
    "in my experience, the reverse",
]


# Topic taxonomy for classification
TOPIC_TAXONOMY = {
    "product-market-fit": [
        "product market fit", "pmf", "finding fit", "market validation",
        "product-market fit", "fit with the market"
    ],
    "growth-strategy": [
        "growth", "scaling", "acquisition", "retention", "viral",
        "growth loops", "flywheel", "network effects"
    ],
    "pricing": [
        "pricing", "monetization", "willingness to pay", "freemium",
        "subscription", "revenue model", "pricing strategy"
    ],
    "hiring": [
        "hiring", "recruiting", "team building", "culture fit",
        "interviewing", "talent", "onboarding"
    ],
    "fundraising": [
        "fundraising", "investors", "series a", "venture capital", "vc",
        "raising money", "pitch deck", "valuation"
    ],
    "leadership": [
        "leadership", "management", "ceo", "founder", "delegation",
        "executive", "decision making", "vision"
    ],
    "user-research": [
        "user research", "customer interviews", "jobs to be done", "jtbd",
        "customer discovery", "user feedback", "qualitative"
    ],
    "experimentation": [
        "a/b test", "experiment", "hypothesis", "data-driven",
        "metrics", "analytics", "measurement"
    ],
    "positioning": [
        "positioning", "differentiation", "category", "messaging",
        "brand", "narrative", "storytelling"
    ],
    "roadmap": [
        "roadmap", "prioritization", "backlog", "planning",
        "strategy", "okrs", "goals"
    ],
    "culture": [
        "culture", "values", "mission", "team dynamics",
        "remote work", "collaboration"
    ],
    "product-development": [
        "product development", "engineering", "technical debt",
        "shipping", "mvp", "iteration", "agile"
    ],
}
