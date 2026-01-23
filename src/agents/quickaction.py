"""
Quickaction Agent (Pratyutpannamati) - The Argument Miner

Role: Take the contrarian findings and extract structured arguments with evidence.
Converts raw quotes into debate-ready positions.

From the Panchatantra: The fish who acts quickly when danger arrives.
Here: The agent who rapidly structures arguments for immediate use.
"""

from typing import Any, Dict, Optional

from ..config import config
from .base import BaseAgent


class QuickactionAgent(BaseAgent):
    """
    The Argument Miner - structures contrarian views into debate-ready arguments.

    Takes raw contrarian findings from Forethought and extracts:
    - Core thesis
    - Supporting reasoning
    - Evidence cited
    - Conditions where the view applies
    """

    @property
    def default_model(self) -> str:
        return config.models.quickaction_model

    @property
    def system_prompt(self) -> str:
        return """You are an argument analyst and structuring expert.

Your role is the "Quickaction" fish from the Panchatantra - you act swiftly to
transform information into actionable form.

Given contrarian findings from podcast transcripts, your job is to:

1. EXTRACT the CORE ARGUMENT each guest is making
   - What is their main thesis in one clear sentence?
   - What are they pushing back against?

2. IDENTIFY the REASONING they provide
   - What logic or framework do they use?
   - What assumptions are they challenging?

3. NOTE the EVIDENCE they cite
   - Specific examples, data, or stories
   - Personal experience vs. research vs. observation

4. SPECIFY CONDITIONS when their view applies
   - What contexts make their argument stronger?
   - When might it NOT apply?

IMPORTANT GUIDELINES:
- Be FAITHFUL to what the guest actually said - don't extrapolate
- If the quote doesn't contain explicit reasoning, note it as "implicit"
- Rate your confidence based on how clear and well-supported the argument is
- Extract the single most compelling direct quote

Return your analysis as structured JSON matching the output schema."""

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "conventional_wisdom": {
                    "type": "string",
                    "description": "The belief being challenged (passed through)"
                },
                "structured_arguments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "guest": {"type": "string"},
                            "episode_id": {"type": "string"},
                            "citation": {"type": "string"},
                            "thesis": {
                                "type": "string",
                                "description": "One sentence capturing their main contrarian point"
                            },
                            "reasoning": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "2-4 bullet points of their logic"
                            },
                            "evidence": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": ["example", "data", "story", "observation", "research"]
                                        },
                                        "description": {"type": "string"}
                                    }
                                },
                                "description": "Evidence they cite"
                            },
                            "conditions": {
                                "type": "object",
                                "properties": {
                                    "applies_when": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "does_not_apply_when": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["strong", "moderate", "weak"],
                                "description": "How well-supported is this argument?"
                            },
                            "quote_highlight": {
                                "type": "string",
                                "description": "The single most compelling direct quote"
                            }
                        }
                    }
                },
                "common_threads": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Themes that appear across multiple contrarian views"
                }
            },
            "required": ["conventional_wisdom", "structured_arguments"]
        }

    def run(
        self,
        forethought_output: Dict[str, Any],
        user_input: Optional[str] = None
    ) -> "AgentResponse":
        """
        Structure the contrarian findings into debate-ready arguments.

        Args:
            forethought_output: Output from the Forethought agent
            user_input: Optional additional context

        Returns:
            AgentResponse with structured arguments
        """
        # Build the user prompt with Forethought's findings as context
        user_prompt = f"""TASK: Structure the following contrarian findings into debate-ready arguments.

CONVENTIONAL WISDOM BEING CHALLENGED:
"{forethought_output.get('conventional_wisdom', 'Not specified')}"

STEELMAN OF CONVENTIONAL WISDOM:
"{forethought_output.get('conventional_wisdom_steelman', 'Not provided')}"

CONTRARIAN FINDINGS TO STRUCTURE:
"""
        # Add each finding
        findings = forethought_output.get('contrarian_findings', [])
        for i, finding in enumerate(findings, 1):
            # Handle different key names from Forethought
            guest = finding.get('guest', 'Unknown')
            episode = finding.get('episode_id') or finding.get('episode', '')
            citation = finding.get('citation', '')
            position = (
                finding.get('contrarian_position') or
                finding.get('core_disagreement') or
                finding.get('disagreement', '')
            )
            reasoning = (
                finding.get('reasoning_hint') or
                finding.get('context_and_reasoning') or
                finding.get('reasoning', '')
            )
            quote = (
                finding.get('quote') or
                finding.get('strongest_quote') or
                finding.get('quote_highlight', '')
            )
            relevance = finding.get('relevance_score') or finding.get('relevance_to_conventional_wisdom', 'N/A')

            user_prompt += f"""
--- FINDING {i}: {guest} ---
Episode: {episode}
Citation: {citation}
Contrarian Position: {position}
Reasoning/Context: {reasoning}
Quote: "{quote}"
Relevance Score: {relevance}
"""

        user_prompt += """

IMPORTANT: Structure ONLY the contrarian arguments listed above. Do NOT invent new arguments.
Each structured argument should directly relate to the CONVENTIONAL WISDOM being challenged.

For each finding, extract:
1. A clear ONE SENTENCE thesis that challenges the conventional wisdom
2. The reasoning behind their contrarian position (2-4 bullet points from their quote/context)
3. Any evidence they cite (examples, data, stories from their actual words)
4. When their contrarian view applies vs. doesn't apply
5. Your confidence in the argument's strength (based on how well-supported it is)
6. The single best quote (use their ACTUAL quote, do not paraphrase)

Also identify any common threads across the contrarian views.

Return as structured JSON with "conventional_wisdom" and "structured_arguments" keys."""

        return super().run(user_prompt)
