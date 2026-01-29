"""
Examiner Agent (Yadbhavishya) - The Debate Architect

Role: Synthesize the structured arguments into a balanced debate format
with a nuanced conclusion about when each perspective applies.

From the Panchatantra: The fish who examines reality as it is.
Here: The agent who synthesizes truth from competing viewpoints.
"""

from typing import Any, Dict, Optional

from ..config import config
from .base import BaseAgent


class ExaminerAgent(BaseAgent):
    """
    The Debate Architect - synthesizes contrarian arguments into balanced wisdom.

    Takes structured arguments from Quickaction and produces:
    - Steelmanned versions of both positions
    - Analysis of the real disagreement
    - Conditions where each view applies
    - A meta-lesson that transcends the debate
    """

    @property
    def default_model(self) -> str:
        return config.models.examiner_model

    @property
    def system_prompt(self) -> str:
        return """You are a debate moderator, synthesizer, and wisdom-seeker.

Your role is the "Examiner" fish from the Panchatantra - you examine reality
as it is, without wishful thinking, to find the deeper truth.

Given structured contrarian arguments from podcast guests, your job is to:

1. STEELMAN BOTH SIDES
   - Present the strongest version of the conventional wisdom
   - Present the strongest version of each contrarian view
   - Don't strawman either position

2. IDENTIFY THE REAL DISAGREEMENT
   - Is it about facts? Values? Definitions? Context?
   - Often debates are about different situations, not true contradictions
   - Find where they're actually talking past each other

3. SYNTHESIZE NUANCED GUIDANCE
   - When does the conventional wisdom hold true?
   - When do the contrarian views apply?
   - What's the meta-lesson that transcends the debate?

4. PRODUCE ACTIONABLE OUTPUT
   - Clear decision criteria for the user
   - Specific questions they should ask themselves
   - Preserve guest names from the source citations

Your goal is NOT to pick a winner but to make the user SMARTER about when
each perspective applies to THEIR specific situation.

IMPORTANT: Your JSON output MUST include these exact keys at the top level:
- "steelman_conventional": {"strongest_case": "...", "supporting_evidence": "..."}
- "steelman_contrarian": {"strongest_case": "...", "supporting_evidence": "..."}
- "real_disagreement": "A single sentence describing the core disagreement"
- "when_conventional_applies": ["condition 1", "condition 2", ...]
- "when_contrarian_applies": ["condition 1", "condition 2", ...]
- "meta_lesson": "A single paragraph with the key insight"
- "questions_to_ask": ["question 1", "question 2", ...]
- "warning_signs": ["sign 1", "sign 2", ...]
- "source_citations": [{"guest": "Guest Name", "episode": "Episode title/ID", "citation": "Guest (timestamp)", "key_insight": "..."}, ...]
- "summary": "2-3 sentence summary of the key takeaway"

CRITICAL: Preserve the guest names, episode IDs, and citations from the input arguments. Do NOT replace them with generic labels.

Return your synthesis as structured JSON."""

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title for the counter-narrative report"
                },
                "conventional_wisdom": {
                    "type": "object",
                    "properties": {
                        "statement": {"type": "string"},
                        "steelman": {
                            "type": "string",
                            "description": "The strongest argument FOR this view"
                        },
                        "core_assumption": {
                            "type": "string",
                            "description": "What this view assumes to be true"
                        }
                    }
                },
                "contrarian_views": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "guest": {"type": "string"},
                            "thesis": {"type": "string"},
                            "steelman": {
                                "type": "string",
                                "description": "Strongest version of their argument"
                            },
                            "key_insight": {
                                "type": "string",
                                "description": "The one thing most worth remembering"
                            },
                            "citation": {"type": "string"},
                            "quote": {"type": "string"}
                        }
                    }
                },
                "synthesis": {
                    "type": "object",
                    "properties": {
                        "real_disagreement": {
                            "type": "string",
                            "description": "What they're actually disagreeing about"
                        },
                        "disagreement_type": {
                            "type": "string",
                            "enum": ["factual", "values", "definitions", "context", "experience"],
                            "description": "The nature of the disagreement"
                        },
                        "conventional_wisdom_applies_when": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "contrarian_view_applies_when": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "meta_lesson": {
                            "type": "string",
                            "description": "The deeper insight that transcends the debate"
                        }
                    }
                },
                "decision_framework": {
                    "type": "object",
                    "properties": {
                        "questions_to_ask_yourself": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Questions to determine which view fits your situation"
                        },
                        "warning_signs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Signs you might be applying the wrong framework"
                        }
                    }
                },
                "summary": {
                    "type": "string",
                    "description": "2-3 sentence summary of the key takeaway"
                }
            },
            "required": ["title", "conventional_wisdom", "contrarian_views", "synthesis", "summary"]
        }

    def run(
        self,
        quickaction_output: Dict[str, Any],
        user_input: Optional[str] = None
    ) -> "AgentResponse":
        """
        Synthesize the structured arguments into a balanced debate.

        Args:
            quickaction_output: Output from the Quickaction agent
            user_input: Optional user context to personalize synthesis

        Returns:
            AgentResponse with synthesized debate
        """
        # Build the user prompt
        user_prompt = f"""TASK: Synthesize these contrarian perspectives into a balanced, actionable report.

CONVENTIONAL WISDOM:
"{quickaction_output.get('conventional_wisdom', 'Not specified')}"

STRUCTURED CONTRARIAN ARGUMENTS:
"""
        # Add each structured argument
        arguments = quickaction_output.get('structured_arguments', [])
        for i, arg in enumerate(arguments, 1):
            # Handle different key names from LLM
            guest = arg.get('guest') or arg.get('guest_name', 'Unknown')
            thesis = arg.get('thesis') or arg.get('core_argument', '')
            citation = arg.get('citation', '')

            # Handle reasoning - could be list or string
            reasoning = arg.get('reasoning', [])
            if isinstance(reasoning, str):
                reasoning = [reasoning]
            reasoning_str = chr(10).join('• ' + str(r) for r in reasoning) if reasoning else '• Not specified'

            # Handle evidence - could be list of dicts, list of strings, or single string
            evidence = arg.get('evidence', [])
            if isinstance(evidence, str):
                evidence_str = f'• {evidence}'
            elif isinstance(evidence, list) and evidence:
                evidence_items = []
                for e in evidence:
                    if isinstance(e, dict):
                        evidence_items.append(f"• [{e.get('type', 'unknown')}] {e.get('description', '')}")
                    else:
                        evidence_items.append(f"• {e}")
                evidence_str = chr(10).join(evidence_items)
            else:
                evidence_str = '• Not specified'

            # Handle conditions - could be dict or nested
            conditions = arg.get('conditions', {})
            if isinstance(conditions, str):
                conditions = {'applies_when': conditions}
            applies = conditions.get('applies_when', [])
            not_applies = conditions.get('does_not_apply_when', [])
            if isinstance(applies, str):
                applies = [applies]
            if isinstance(not_applies, str):
                not_applies = [not_applies]

            quote = arg.get('quote_highlight') or arg.get('best_quote') or arg.get('strongest_quote', '')

            user_prompt += f"""
--- ARGUMENT {i}: {guest} ---
Citation: {citation}

THESIS: {thesis}

REASONING:
{reasoning_str}

EVIDENCE:
{evidence_str}

APPLIES WHEN: {', '.join(str(a) for a in applies) if applies else 'Not specified'}
DOES NOT APPLY WHEN: {', '.join(str(a) for a in not_applies) if not_applies else 'Not specified'}

CONFIDENCE: {arg.get('confidence', 'N/A')}
KEY QUOTE: "{quote}"
"""

        common_threads = quickaction_output.get('common_threads', [])
        if common_threads:
            user_prompt += f"""
COMMON THREADS ACROSS ARGUMENTS:
{chr(10).join('• ' + t for t in common_threads)}
"""

        if user_input:
            user_prompt += f"""
USER'S CONTEXT:
{user_input}
"""

        user_prompt += """

YOUR SYNTHESIS SHOULD:
1. Steelman BOTH the conventional wisdom AND the contrarian views
2. Identify what they're REALLY disagreeing about (facts? values? context?)
3. Provide clear guidance on WHEN each view applies
4. Extract a meta-lesson that helps the user think more clearly
5. Give specific questions they can ask themselves

Return as structured JSON."""

        return super().run(user_prompt)
