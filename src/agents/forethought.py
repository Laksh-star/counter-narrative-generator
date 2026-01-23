"""
Forethought Agent (Anagatavidhata) - The Contrarian Scout

Role: Given a conventional wisdom statement, find podcast guests who disagree
or offer alternative perspectives.

From the Panchatantra: The fish who plans ahead and sees danger coming.
Here: The agent who scouts for contrarian views before they're needed.
"""

from typing import Any, Dict, List, Optional

from ..config import config
from ..data.vectorstore import VectorStore
from .base import BaseAgent, AgentResponse


class ForethoughtAgent(BaseAgent):
    """
    The Contrarian Scout - finds podcast guests who challenge conventional wisdom.

    Uses RAG to search the Lenny's Podcast transcript database for dissenting
    views, then structures the findings for the next agent.
    """

    def __init__(
        self,
        vectorstore: VectorStore,
        model: Optional[str] = None
    ):
        """
        Initialize the Forethought agent.

        Args:
            vectorstore: The VectorStore instance for searching
            model: Optional model override
        """
        super().__init__(model)
        self.vectorstore = vectorstore

    @property
    def default_model(self) -> str:
        return config.models.forethought_model

    @property
    def system_prompt(self) -> str:
        return """You are a research analyst specializing in finding contrarian perspectives.

Your role is the "Forethought" fish from the Panchatantra - you plan ahead by finding
diverse viewpoints before they're urgently needed.

Given:
1. A statement of "conventional wisdom" (what most people believe)
2. Search results from podcast transcripts

Your job is to:
1. Identify which search results contain GENUINE contrarian views
2. Extract the core disagreement or nuance each guest offers
3. Note the context and reasoning behind their position
4. Rank by how compelling and distinct each perspective is

IMPORTANT GUIDELINES:
- Don't include results that actually AGREE with the conventional wisdom
- Look for nuanced disagreement, not just surface-level contradiction
- Prioritize guests who explain WHY they disagree with evidence
- One perspective per guest (pick their strongest contrarian point)

Return your analysis as structured JSON matching the output schema."""

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "conventional_wisdom": {
                    "type": "string",
                    "description": "The conventional belief being challenged"
                },
                "conventional_wisdom_steelman": {
                    "type": "string",
                    "description": "The strongest argument FOR the conventional wisdom"
                },
                "contrarian_findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "guest": {"type": "string"},
                            "episode_id": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "citation": {"type": "string"},
                            "quote": {"type": "string", "description": "Key quote from the transcript"},
                            "contrarian_position": {"type": "string", "description": "Their main disagreement"},
                            "reasoning_hint": {"type": "string", "description": "Why they hold this view"},
                            "relevance_score": {"type": "number", "minimum": 1, "maximum": 10},
                        }
                    }
                },
                "search_quality": {
                    "type": "string",
                    "enum": ["excellent", "good", "fair", "poor"],
                    "description": "How well the search results matched the query"
                }
            },
            "required": ["conventional_wisdom", "contrarian_findings", "search_quality"]
        }

    def run(
        self,
        conventional_wisdom: str,
        filter_topics: Optional[List[str]] = None,
        n_results: int = 8
    ) -> AgentResponse:
        """
        Find contrarian perspectives on the given conventional wisdom.

        Args:
            conventional_wisdom: The belief to find counter-arguments for
            filter_topics: Optional topics to filter by
            n_results: Number of contrarian results to find

        Returns:
            AgentResponse with contrarian findings
        """
        # First, search the vector store for contrarian content
        search_results = self.vectorstore.search_contrarian(
            conventional_wisdom=conventional_wisdom,
            n_results=n_results,
            filter_topics=filter_topics,
        )

        # Format search results for the LLM
        search_context = self._format_search_results(search_results)

        # Build the user prompt
        user_prompt = f"""CONVENTIONAL WISDOM TO CHALLENGE:
"{conventional_wisdom}"

SEARCH RESULTS FROM LENNY'S PODCAST:
{search_context}

Analyze these search results and identify genuine contrarian perspectives.
Return structured JSON with your findings.

Remember:
- Only include results that actually DISAGREE with or provide important nuance to the conventional wisdom
- Extract the strongest quote that captures their contrarian position
- Rate relevance 1-10 based on how directly they challenge the conventional wisdom"""

        # Run through the LLM
        return super().run(user_prompt)

    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for the LLM prompt"""
        if not results:
            return "No relevant results found."

        formatted = []
        for i, r in enumerate(results, 1):
            contrarian_note = " [HAS CONTRARIAN SIGNAL]" if r.get("has_contrarian_signal") else ""
            signals = ", ".join(r.get("contrarian_signals", [])) if r.get("contrarian_signals") else "none detected"

            formatted.append(f"""
--- RESULT {i} ---
Guest: {r['guest']}
Episode: {r['episode_id']}
Citation: {r['citation']}
Similarity Score: {r['similarity']:.3f}
Contrarian Signals: {signals}{contrarian_note}
Topics: {', '.join(r.get('topics', [])) or 'unclassified'}

TEXT:
{r['text'][:2000]}
""")

        return "\n".join(formatted)
