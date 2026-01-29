"""
ChromaDB Vector Store for Lenny's Podcast chunks
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from openai import OpenAI
from tqdm import tqdm

from ..config import config
from .prepare_chunks import enrich_chunk, EnrichedChunk


class VectorStore:
    """ChromaDB-based vector store for podcast chunks"""

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        persist_dir = persist_directory or config.chroma.persist_directory

        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection with cosine distance for embeddings
        # ChromaDB uses cosine distance when hnsw:space is set to "cosine"
        self.collection = self.client.get_or_create_collection(
            name=config.chroma.collection_name,
            metadata={
                "hnsw:space": "cosine",  # Use cosine distance for embeddings
                "description": "Lenny's Podcast transcript chunks"
            }
        )

        # Initialize OpenRouter client for embeddings
        self.openai_client = OpenAI(
            api_key=config.models.api_key,
            base_url=config.models.base_url,
        )

    def is_loaded(self) -> bool:
        """Check if the vector store has data loaded"""
        return self.collection.count() > 0

    def load_from_file(self, chunks_path: str, force_reload: bool = False) -> int:
        """Alias for load_chunks() for backwards compatibility"""
        return self.load_chunks(chunks_path, force_reload)

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenRouter"""
        response = self.openai_client.embeddings.create(
            input=text,
            model=config.models.embedding_model,
        )
        return response.data[0].embedding

    def _get_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.openai_client.embeddings.create(
                input=batch,
                model=config.models.embedding_model,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def load_chunks(self, chunks_path: str, force_reload: bool = False) -> int:
        """
        Load chunks from JSONL file into ChromaDB.

        Args:
            chunks_path: Path to chunks.jsonl
            force_reload: If True, delete existing data and reload

        Returns:
            Number of chunks loaded
        """
        # Check if already loaded
        existing_count = self.collection.count()
        if existing_count > 0 and not force_reload:
            print(f"✅ Collection already has {existing_count:,} chunks. Use force_reload=True to reload.")
            return existing_count

        if force_reload and existing_count > 0:
            print(f"🗑️  Deleting existing {existing_count:,} chunks...")
            # Delete all by getting all IDs
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)

        print(f"📂 Loading chunks from {chunks_path}...")

        # Read and enrich all chunks
        chunks = []
        with open(chunks_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    raw = json.loads(line)
                    enriched = enrich_chunk(raw)
                    chunks.append(enriched)

        print(f"   Found {len(chunks):,} chunks")

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{chunk.episode_id}_{chunk.chunk_id}"
            ids.append(chunk_id)
            documents.append(chunk.text)

            # Metadata (ChromaDB has limits on metadata size)
            metadata = {
                "episode_id": chunk.episode_id,
                "guest": chunk.title,
                "speaker_primary": chunk.speaker_primary,
                "t_start": chunk.t_start,
                "t_end": chunk.t_end,
                "citation": chunk.citation,
                "has_contrarian_signal": chunk.has_contrarian_signal,
                "topics": ",".join(chunk.topics) if chunk.topics else "",
                "contrarian_signals": ",".join(chunk.contrarian_signals_found) if chunk.contrarian_signals_found else "",
            }
            metadatas.append(metadata)

        # Generate embeddings in batches
        print(f"🔢 Generating embeddings...")
        embeddings = []

        batch_size = 50  # Smaller batches for stability
        for i in tqdm(range(0, len(documents), batch_size), desc="Embedding"):
            batch_texts = documents[i:i + batch_size]
            batch_embeddings = self._get_embeddings_batch(batch_texts, batch_size=batch_size)
            embeddings.extend(batch_embeddings)

        # Add to ChromaDB in batches
        print(f"💾 Storing in ChromaDB...")
        add_batch_size = 500

        for i in tqdm(range(0, len(ids), add_batch_size), desc="Storing"):
            end_idx = min(i + add_batch_size, len(ids))
            self.collection.add(
                ids=ids[i:end_idx],
                documents=documents[i:end_idx],
                embeddings=embeddings[i:end_idx],
                metadatas=metadatas[i:end_idx],
            )

        final_count = self.collection.count()
        print(f"✅ Loaded {final_count:,} chunks into ChromaDB")

        return final_count

    def search(
        self,
        query: str,
        n_results: int = 10,
        filter_topics: Optional[List[str]] = None,
        prefer_contrarian: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks.

        Args:
            query: Search query text
            n_results: Maximum number of results
            filter_topics: Optional list of topics to filter by
            prefer_contrarian: If True, boost results with contrarian signals

        Returns:
            List of matching chunks with scores
        """
        # Generate query embedding
        query_embedding = self._get_embedding(query)

        # Build where filter
        where_filter = None
        if filter_topics:
            # ChromaDB uses $contains for partial string matching
            # We'll filter post-query since topics is comma-separated
            pass

        # Query ChromaDB
        # Get more results if we need to filter/re-rank and dedupe by guest
        # Need extra results since we dedupe by guest (1 per guest)
        fetch_n = n_results * 10 if prefer_contrarian else n_results * 3

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_n,
            include=["documents", "metadatas", "distances"],
        )

        # Process results
        processed = []
        for i, doc_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            # Convert distance to similarity score (ChromaDB uses L2 distance by default)
            # For cosine distance: similarity = 1 - distance
            similarity = 1 - distance

            # Filter by topics if specified
            if filter_topics:
                chunk_topics = metadata.get("topics", "").split(",")
                if not any(t in chunk_topics for t in filter_topics):
                    continue

            # Boost contrarian results if requested
            if prefer_contrarian and metadata.get("has_contrarian_signal"):
                similarity *= 1.2  # 20% boost

            processed.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "guest": metadata.get("guest", "Unknown"),
                "episode_id": metadata.get("episode_id", ""),
                "speaker_primary": metadata.get("speaker_primary", ""),
                "t_start": metadata.get("t_start", 0),
                "citation": metadata.get("citation", ""),
                "has_contrarian_signal": metadata.get("has_contrarian_signal", False),
                "contrarian_signals": metadata.get("contrarian_signals", "").split(",") if metadata.get("contrarian_signals") else [],
                "topics": metadata.get("topics", "").split(",") if metadata.get("topics") else [],
                "similarity": similarity,
            })

        # Sort by similarity and dedupe by guest
        processed.sort(key=lambda x: x["similarity"], reverse=True)

        # Deduplicate by guest (one result per guest for diversity)
        seen_guests = set()
        deduped = []
        for result in processed:
            guest = result["guest"]
            if guest not in seen_guests:
                seen_guests.add(guest)
                deduped.append(result)
            if len(deduped) >= n_results:
                break

        return deduped

    def search_contrarian(
        self,
        conventional_wisdom: str,
        n_results: int = 5,
        filter_topics: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search specifically for contrarian views on a topic.

        Args:
            conventional_wisdom: The conventional belief to find contrarians for
            n_results: Number of contrarian perspectives to return
            filter_topics: Optional topic filter

        Returns:
            List of chunks with contrarian perspectives
        """
        # Craft a query that emphasizes finding disagreement
        contrarian_query = f"""
        Perspectives that disagree with, challenge, or provide nuance to the idea that:
        {conventional_wisdom}

        Arguments against this view. Counterpoints. Alternative perspectives.
        People who say this is wrong, overrated, or missing something important.
        """

        return self.search(
            query=contrarian_query,
            n_results=n_results,
            filter_topics=filter_topics,
            prefer_contrarian=True,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        count = self.collection.count()

        # Sample some metadata to get topic distribution
        sample = self.collection.get(limit=min(1000, count), include=["metadatas"])

        topic_counts = {}
        contrarian_count = 0

        for metadata in sample["metadatas"]:
            if metadata.get("has_contrarian_signal"):
                contrarian_count += 1
            topics = metadata.get("topics", "").split(",")
            for topic in topics:
                if topic:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return {
            "total_chunks": count,
            "sample_size": len(sample["metadatas"]),
            "contrarian_in_sample": contrarian_count,
            "topic_distribution": dict(sorted(topic_counts.items(), key=lambda x: -x[1])),
        }
