"""
Data preparation: Enrich chunks with contrarian signals and topic tags
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from pathlib import Path

from ..config import CONTRARIAN_SIGNALS, TOPIC_TAXONOMY


@dataclass
class EnrichedChunk:
    """Enriched chunk with metadata for contrarian retrieval"""

    # Original fields
    episode_id: str
    title: str  # Guest name
    chunk_id: int
    t_start: int
    t_end: int
    speakers: List[str]
    text: str

    # Enriched fields
    speaker_primary: str  # Main non-Lenny speaker
    has_contrarian_signal: bool
    contrarian_signals_found: List[str]
    topics: List[str]
    citation: str  # "Guest Name (12:34)"

    def to_dict(self) -> dict:
        return asdict(self)


def detect_contrarian_signals(text: str) -> List[str]:
    """Detect phrases indicating contrarian/disagreement stance"""
    text_lower = text.lower()
    found = []
    for signal in CONTRARIAN_SIGNALS:
        if signal in text_lower:
            found.append(signal)
    return found


def classify_topics(text: str) -> List[str]:
    """Classify chunk by business topics"""
    text_lower = text.lower()
    topics = []
    for topic, keywords in TOPIC_TAXONOMY.items():
        if any(kw in text_lower for kw in keywords):
            topics.append(topic)
    return topics


def extract_primary_speaker(speakers: List[str]) -> str:
    """Get the main non-Lenny, non-Narration speaker"""
    for speaker in speakers:
        if speaker and speaker not in ["Lenny", "Narration", None, ""]:
            return speaker
    return speakers[0] if speakers else "Unknown"


def format_timestamp(seconds: int) -> str:
    """Convert seconds to MM:SS format"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def enrich_chunk(raw_chunk: dict) -> EnrichedChunk:
    """Enrich a raw chunk with metadata for better retrieval"""

    speakers = raw_chunk.get("speakers", [])
    text = raw_chunk.get("text", "")
    t_start = raw_chunk.get("t_start", 0)

    # Extract primary speaker
    primary_speaker = extract_primary_speaker(speakers)

    # Detect contrarian signals
    signals = detect_contrarian_signals(text)

    # Classify topics
    topics = classify_topics(text)

    # Format citation
    citation = f"{raw_chunk.get('title', 'Unknown')} ({format_timestamp(t_start)})"

    return EnrichedChunk(
        episode_id=raw_chunk.get("episode_id", ""),
        title=raw_chunk.get("title", ""),
        chunk_id=raw_chunk.get("chunk_id", 0),
        t_start=t_start,
        t_end=raw_chunk.get("t_end", 0),
        speakers=speakers,
        text=text,
        speaker_primary=primary_speaker,
        has_contrarian_signal=len(signals) > 0,
        contrarian_signals_found=signals,
        topics=topics,
        citation=citation,
    )


def process_chunks_file(
    input_path: str,
    output_path: Optional[str] = None
) -> List[EnrichedChunk]:
    """
    Process chunks.jsonl and enrich with metadata.

    Args:
        input_path: Path to chunks.jsonl
        output_path: Optional path to write enriched chunks

    Returns:
        List of EnrichedChunk objects
    """
    enriched_chunks = []

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                raw_chunk = json.loads(line)
                enriched = enrich_chunk(raw_chunk)
                enriched_chunks.append(enriched)

    # Optionally write to file
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in enriched_chunks:
                f.write(json.dumps(chunk.to_dict()) + '\n')

    # Print stats
    total = len(enriched_chunks)
    with_signals = sum(1 for c in enriched_chunks if c.has_contrarian_signal)
    topics_count = {}
    for chunk in enriched_chunks:
        for topic in chunk.topics:
            topics_count[topic] = topics_count.get(topic, 0) + 1

    print(f"\n📊 Chunk Enrichment Stats:")
    print(f"   Total chunks: {total:,}")
    print(f"   With contrarian signals: {with_signals:,} ({with_signals/total*100:.1f}%)")
    print(f"\n   Topics distribution:")
    for topic, count in sorted(topics_count.items(), key=lambda x: -x[1])[:10]:
        print(f"   - {topic}: {count:,}")

    return enriched_chunks


if __name__ == "__main__":
    import sys

    input_file = sys.argv[1] if len(sys.argv) > 1 else "content/output/chunks.jsonl"
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    chunks = process_chunks_file(input_file, output_file)
    print(f"\n✅ Processed {len(chunks)} chunks")
