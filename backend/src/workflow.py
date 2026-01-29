"""
Counter-Narrative Generator Workflow

Orchestrates the Three-Fish agents in sequence:
1. Forethought (Scout) - Finds contrarian perspectives
2. Quickaction (Miner) - Structures the arguments
3. Examiner (Architect) - Synthesizes the debate

Inspired by the Panchatantra tale and Andrew Ng's agentic workflows.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .data.vectorstore import VectorStore
from .agents import ForethoughtAgent, QuickactionAgent, ExaminerAgent
from .agents.base import AgentResponse


@dataclass
class WorkflowResult:
    """Complete result from the Counter-Narrative workflow"""

    # Input
    conventional_wisdom: str
    topics_filter: Optional[List[str]]

    # Outputs from each agent
    forethought_output: Dict[str, Any]
    quickaction_output: Dict[str, Any]
    examiner_output: Dict[str, Any]

    # Metadata
    success: bool
    total_tokens: Dict[str, int]
    execution_time_ms: int
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conventional_wisdom": self.conventional_wisdom,
            "topics_filter": self.topics_filter,
            "forethought": self.forethought_output,
            "quickaction": self.quickaction_output,
            "examiner": self.examiner_output,
            "metadata": {
                "success": self.success,
                "total_tokens": self.total_tokens,
                "execution_time_ms": self.execution_time_ms,
                "errors": self.errors,
            }
        }

    def get_report(self) -> Dict[str, Any]:
        """Get just the final synthesized report"""
        return self.examiner_output


class CounterNarrativeWorkflow:
    """
    The Three-Fish Workflow for mining contrarian wisdom.

    Usage:
        workflow = CounterNarrativeWorkflow(vectorstore)
        result = workflow.run("Everyone says you need PMF before scaling")
        print(result.get_report())
    """

    def __init__(self, vectorstore: VectorStore):
        """
        Initialize the workflow with a vector store.

        Args:
            vectorstore: Loaded VectorStore with podcast chunks
        """
        self.vectorstore = vectorstore

        # Initialize agents
        self.forethought = ForethoughtAgent(vectorstore)
        self.quickaction = QuickactionAgent()
        self.examiner = ExaminerAgent()

    def run(
        self,
        conventional_wisdom: str,
        filter_topics: Optional[List[str]] = None,
        n_contrarian_results: int = 5,
        user_context: Optional[str] = None,
        verbose: bool = False,
    ) -> WorkflowResult:
        """
        Execute the full Counter-Narrative workflow.

        Args:
            conventional_wisdom: The belief to find contrarian views on
            filter_topics: Optional topics to filter by
            n_contrarian_results: How many contrarian perspectives to find
            user_context: Optional context about the user's situation
            verbose: Print progress updates

        Returns:
            WorkflowResult with all agent outputs
        """
        start_time = datetime.now()
        errors = []
        total_tokens = {"prompt": 0, "completion": 0}

        # Initialize outputs
        forethought_data = {}
        quickaction_data = {}
        examiner_data = {}

        # ============================================
        # STAGE 1: FORETHOUGHT (Contrarian Scout)
        # ============================================
        if verbose:
            print(f"\n🔍 FORETHOUGHT: Searching for contrarian perspectives...")

        forethought_response = self.forethought.run(
            conventional_wisdom=conventional_wisdom,
            filter_topics=filter_topics,
            n_results=n_contrarian_results,
        )

        if forethought_response.success:
            forethought_data = forethought_response.data
            total_tokens["prompt"] += forethought_response.usage.get("prompt_tokens", 0)
            total_tokens["completion"] += forethought_response.usage.get("completion_tokens", 0)

            # Handle case where LLM returns a list directly instead of a dict
            if isinstance(forethought_data, list):
                forethought_data = {"contrarian_findings": forethought_data}

            # Handle different key names the LLM might use
            findings = (
                forethought_data.get("contrarian_findings") or
                forethought_data.get("contrarian_perspectives") or
                forethought_data.get("findings") or
                []
            )
            # Normalize the key name
            forethought_data["contrarian_findings"] = findings

            if verbose:
                print(f"   Found {len(findings)} contrarian perspectives")
                for f in findings[:3]:
                    print(f"   - {f.get('guest', 'Unknown')}: {f.get('contrarian_position', '')[:60]}...")
        else:
            errors.append(f"Forethought failed: {forethought_response.error}")
            if verbose:
                print(f"   ❌ Error: {forethought_response.error}")

        # Check if we have enough contrarian findings to continue
        findings = forethought_data.get("contrarian_findings", [])
        if not findings:
            return WorkflowResult(
                conventional_wisdom=conventional_wisdom,
                topics_filter=filter_topics,
                forethought_output=forethought_data,
                quickaction_output={},
                examiner_output={},
                success=False,
                total_tokens=total_tokens,
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                errors=errors + ["No contrarian perspectives found"],
            )

        # ============================================
        # STAGE 2: QUICKACTION (Argument Miner)
        # ============================================
        if verbose:
            print(f"\n⚡ QUICKACTION: Structuring arguments...")

        quickaction_response = self.quickaction.run(
            forethought_output=forethought_data,
        )

        if quickaction_response.success:
            quickaction_data = quickaction_response.data
            total_tokens["prompt"] += quickaction_response.usage.get("prompt_tokens", 0)
            total_tokens["completion"] += quickaction_response.usage.get("completion_tokens", 0)

            # Handle case where LLM returns a list directly
            if isinstance(quickaction_data, list):
                quickaction_data = {"structured_arguments": quickaction_data}

            if verbose:
                arguments = quickaction_data.get("structured_arguments", [])
                print(f"   Structured {len(arguments)} arguments")
                threads = quickaction_data.get("common_threads", [])
                if threads:
                    print(f"   Common threads: {', '.join(str(t)[:50] for t in threads[:3])}")
        else:
            errors.append(f"Quickaction failed: {quickaction_response.error}")
            if verbose:
                print(f"   ❌ Error: {quickaction_response.error}")

        # ============================================
        # STAGE 3: EXAMINER (Debate Architect)
        # ============================================
        if verbose:
            print(f"\n🎯 EXAMINER: Synthesizing debate...")

        examiner_response = self.examiner.run(
            quickaction_output=quickaction_data,
            user_input=user_context,
        )

        if examiner_response.success:
            examiner_data = examiner_response.data
            total_tokens["prompt"] += examiner_response.usage.get("prompt_tokens", 0)
            total_tokens["completion"] += examiner_response.usage.get("completion_tokens", 0)

            if verbose:
                synthesis = examiner_data.get("synthesis", {})
                real_disagreement = str(synthesis.get('real_disagreement', 'N/A'))
                meta_lesson = str(synthesis.get('meta_lesson', 'N/A'))
                print(f"   Real disagreement: {real_disagreement[:80]}...")
                print(f"   Meta-lesson: {meta_lesson[:80]}...")
        else:
            errors.append(f"Examiner failed: {examiner_response.error}")
            if verbose:
                print(f"   ❌ Error: {examiner_response.error}")

        # ============================================
        # COMPILE RESULTS
        # ============================================
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        if verbose:
            print(f"\n✅ Workflow complete in {execution_time}ms")
            print(f"   Total tokens: {total_tokens['prompt'] + total_tokens['completion']:,}")

        return WorkflowResult(
            conventional_wisdom=conventional_wisdom,
            topics_filter=filter_topics,
            forethought_output=forethought_data,
            quickaction_output=quickaction_data,
            examiner_output=examiner_data,
            success=len(errors) == 0,
            total_tokens=total_tokens,
            execution_time_ms=execution_time,
            errors=errors,
        )


def _safe_str(value, default="N/A", max_len=800) -> str:
    """Safely convert a value to a string, handling nested dicts"""
    if value is None:
        return default
    if isinstance(value, str):
        return value[:max_len] if len(value) > max_len else value
    if isinstance(value, dict):
        # Try to extract a meaningful string from common keys
        for key in ["statement", "text", "content", "description", "core_insight", "summary"]:
            if key in value and isinstance(value[key], str):
                return value[key][:max_len]
        # Fallback: return first string value found
        for v in value.values():
            if isinstance(v, str):
                return v[:max_len]
        return str(value)[:max_len]
    if isinstance(value, list):
        return ", ".join(str(item)[:100] for item in value[:5])
    return str(value)[:max_len]


def format_report_text(result: WorkflowResult) -> str:
    """Format the workflow result as human-readable text"""

    report = result.examiner_output
    if not report:
        return "No report generated. Check errors in the workflow result."

    # Handle case where everything is nested under 'synthesis' key
    if list(report.keys()) == ['synthesis'] and isinstance(report.get('synthesis'), dict):
        report = report['synthesis']

    lines = []
    lines.append("=" * 70)
    lines.append(f"🎯 COUNTER-NARRATIVE REPORT")
    lines.append(f"   {_safe_str(report.get('title'), 'Untitled')}")
    lines.append("=" * 70)

    # Conventional Wisdom - handle multiple possible structures
    cw = report.get("conventional_wisdom", {})
    if isinstance(cw, str):
        cw = {"statement": cw}
    lines.append(f"\n📌 CONVENTIONAL WISDOM:")
    cw_statement = cw.get("statement") if isinstance(cw, dict) else result.conventional_wisdom
    lines.append(f'   "{_safe_str(cw_statement, result.conventional_wisdom)}"')

    # Steelman of conventional wisdom - check multiple keys
    steelman_conv = report.get('steelman_conventional', {})
    steelmanned_positions = report.get('steelmanned_positions', {})
    steelman = (
        cw.get('steelman') if isinstance(cw, dict) else None
    ) or (
        cw.get('strongest_case') if isinstance(cw, dict) else None
    ) or steelman_conv.get('strongest_case') or (
        steelmanned_positions.get('conventional_wisdom', {}).get('strongest_case')
    )
    if steelman:
        lines.append(f"\n   Steelman: {_safe_str(steelman, max_len=1000)}")

    # Contrarian Views - handle multiple possible structures
    lines.append(f"\n🔴 CONTRARIAN PERSPECTIVES:")
    contrarian_views = report.get("contrarian_views", [])
    if not contrarian_views:
        # Try alternate keys from different output formats
        contrarian_views = (
            report.get("contrarian_arguments", []) or
            report.get("perspectives", [])
        )

    # Handle steelman_contrarian format (dict with strongest_case, supporting_evidence)
    steelman_contrarian = report.get("steelman_contrarian", {})
    # Also check steelmanned_positions.contrarian_view
    if not steelman_contrarian:
        steelmanned_positions = report.get('steelmanned_positions', {})
        steelman_contrarian = steelmanned_positions.get('contrarian_view', {})

    has_contrarian_content = False

    if steelman_contrarian:
        # Extract from steelman_contrarian format
        strongest = steelman_contrarian.get('strongest_case', '')
        if strongest:
            has_contrarian_content = True
            lines.append(f"\n   ▸ Steelmanned Contrarian Case:")
            lines.append(f"     {_safe_str(strongest, max_len=1000)}")
            evidence = steelman_contrarian.get('supporting_evidence', '')
            if evidence:
                lines.append(f"\n     Evidence: {_safe_str(evidence, max_len=800)}")

    # Handle source_citations format (list of dicts with guest, episode, citation, key_insight)
    source_citations = report.get("source_citations", [])
    if source_citations and isinstance(source_citations, list):
        lines.append(f"\n   Individual Guest Perspectives:")
        for citation in source_citations:
            has_contrarian_content = True
            if isinstance(citation, dict):
                guest = citation.get('guest') or citation.get('source', 'Unknown')
                episode = citation.get('episode', '')
                cite_ref = citation.get('citation', '')
                perspective = citation.get('perspective', '')
                insight = citation.get('key_insight', '')

                lines.append(f"\n   ▸ {guest}:")
                if episode:
                    lines.append(f"     Episode: {episode}")
                if cite_ref:
                    lines.append(f"     Citation: {cite_ref}")
                if perspective:
                    lines.append(f"     [{perspective}]")
                if insight:
                    lines.append(f"     {_safe_str(insight)}")

    # Also extract from citations dict if available (has guest names as keys)
    citations = report.get("citations", {})
    if citations and isinstance(citations, dict) and not source_citations:
        lines.append(f"\n   Individual Guest Perspectives:")
        for guest, insight in citations.items():
            has_contrarian_content = True
            guest_name = guest.replace("_", " ").title()
            lines.append(f"\n   ▸ {guest_name}:")
            lines.append(f"     {_safe_str(insight)}")

    # Handle standard contrarian_views array format
    for view in contrarian_views:
        has_contrarian_content = True
        if isinstance(view, str):
            lines.append(f"\n   ▸ {view}")
            continue
        lines.append(f"\n   ▸ {_safe_str(view.get('guest'), 'Unknown')}")
        lines.append(f"     Thesis: {_safe_str(view.get('thesis') or view.get('position'))}")
        lines.append(f"     Key Insight: {_safe_str(view.get('key_insight') or view.get('insight'))}")
        quote = view.get("quote") or view.get("quote_highlight") or ""
        if quote:
            lines.append(f'     Quote: "{_safe_str(quote, max_len=150)}"')
        citation = view.get('citation') or view.get('episode_id') or ''
        if citation:
            lines.append(f"     [{citation}]")

    if not has_contrarian_content:
        lines.append(f"   (No contrarian perspectives extracted)")

    # Synthesis - handle multiple possible structures
    synthesis = report.get("synthesis", {})
    if isinstance(synthesis, str):
        synthesis = {"real_disagreement": synthesis}

    lines.append(f"\n⚖️ SYNTHESIS:")

    # Real disagreement - check multiple locations (examiner puts it at top level too)
    real_disagreement_obj = report.get('real_disagreement', {}) or {}
    real_disagreement = None

    # First check if it's a simple string at top level
    if isinstance(real_disagreement_obj, str):
        real_disagreement = real_disagreement_obj
    elif isinstance(real_disagreement_obj, dict):
        real_disagreement = real_disagreement_obj.get('core_tension')

    # Fall back to synthesis keys
    if not real_disagreement:
        real_disagreement = (
            synthesis.get('real_disagreement') or
            synthesis.get('core_tension')
        )

    # Handle nested dict
    if isinstance(real_disagreement, dict):
        real_disagreement = real_disagreement.get('core_tension') or real_disagreement.get('explanation') or str(list(real_disagreement.values())[0] if real_disagreement else "N/A")

    lines.append(f"   Real Disagreement: {_safe_str(real_disagreement)}")

    # Key dimensions of disagreement (examiner puts it in real_disagreement.key_dimensions)
    key_dimensions = []
    if isinstance(real_disagreement_obj, dict):
        key_dimensions = real_disagreement_obj.get('key_dimensions', [])
    if not key_dimensions:
        key_dimensions = synthesis.get('key_dimensions', [])
    if key_dimensions:
        lines.append(f"\n   Key Dimensions:")
        for dim in key_dimensions[:4]:
            lines.append(f"      • {_safe_str(dim, max_len=100)}")

    # Disagreement type
    disagreement_types = synthesis.get('disagreement_type') or synthesis.get('type')
    if isinstance(real_disagreement, dict) and 'disagreement_types' in synthesis.get('real_disagreement', {}):
        dt = synthesis['real_disagreement']['disagreement_types']
        if isinstance(dt, list):
            disagreement_types = ", ".join(str(t).split(":")[0] for t in dt[:3])
    if disagreement_types:
        lines.append(f"   Type: {_safe_str(disagreement_types)}")

    # When conventional wisdom applies - check multiple possible keys
    lines.append(f"\n   ✅ Conventional wisdom applies when:")

    # Check synthesis_framework nested structure
    synthesis_framework = report.get("synthesis_framework", {})
    vc_path = synthesis_framework.get("when_vc_path_applies", {})

    cw_applies = (
        report.get("when_conventional_applies") or
        synthesis.get("conventional_wisdom_applies_when") or
        synthesis.get("when_conventional_applies") or
        synthesis.get("when_to_use_conventional") or
        (synthesis.get("contextual_guidance", {}) or {}).get("when_conventional_wisdom_applies") or
        []
    )

    # If empty, try to extract from synthesis_framework
    if not cw_applies and vc_path:
        cw_applies = []
        for category, items in vc_path.items():
            if isinstance(items, list):
                cw_applies.extend(items[:2])  # Take up to 2 from each category

    # Also try decision_framework.when_vc_applies
    if not cw_applies:
        df = report.get("decision_framework", {})
        cw_applies = df.get("when_vc_applies", []) or df.get("vc_path_indicators", [])

    # Ensure it's a list
    if isinstance(cw_applies, dict):
        cw_applies = list(cw_applies.values())
    elif isinstance(cw_applies, str):
        cw_applies = [cw_applies]
    if cw_applies and isinstance(cw_applies, list):
        for condition in cw_applies[:5]:
            lines.append(f"      • {_safe_str(condition, max_len=100)}")
    else:
        lines.append(f"      • (See full output for details)")

    # When contrarian view applies
    lines.append(f"\n   ❌ Contrarian view applies when:")

    bootstrap_path = synthesis_framework.get("when_bootstrap_path_applies", {})

    cv_applies = (
        report.get("when_contrarian_applies") or
        synthesis.get("contrarian_view_applies_when") or
        synthesis.get("when_contrarian_applies") or
        synthesis.get("when_to_use_contrarian") or
        (synthesis.get("contextual_guidance", {}) or {}).get("when_contrarian_view_applies") or
        []
    )

    # If empty, try to extract from synthesis_framework
    if not cv_applies and bootstrap_path:
        cv_applies = []
        for category, items in bootstrap_path.items():
            if isinstance(items, list):
                cv_applies.extend(items[:2])  # Take up to 2 from each category

    # Also try decision_framework.when_bootstrap_applies
    if not cv_applies:
        df = report.get("decision_framework", {})
        cv_applies = df.get("when_bootstrap_applies", []) or df.get("bootstrap_path_indicators", [])

    # Ensure it's a list
    if isinstance(cv_applies, dict):
        cv_applies = list(cv_applies.values())
    elif isinstance(cv_applies, str):
        cv_applies = [cv_applies]
    if cv_applies and isinstance(cv_applies, list):
        for condition in cv_applies[:5]:
            lines.append(f"      • {_safe_str(condition, max_len=100)}")
    else:
        lines.append(f"      • (See full output for details)")

    # Meta-lesson
    lines.append(f"\n   💡 META-LESSON:")
    meta_lesson = (
        synthesis.get('meta_lesson') or
        report.get('meta_lesson') or
        synthesis.get('key_insight') or
        synthesis.get('conclusion')
    )
    lines.append(f"      {_safe_str(meta_lesson, max_len=1200)}")

    # Decision Framework - check multiple locations
    framework = report.get("decision_framework", {}) or report.get("actionable_guidance", {})
    if framework:
        # Questions to ask
        questions = (
            framework.get("questions_to_ask_yourself") or
            framework.get("questions_to_ask") or
            framework.get("critical_questions") or
            framework.get("decision_criteria") or
            framework.get("self_assessment_questions") or
            []
        )
        # Ensure it's a list
        if isinstance(questions, dict):
            questions = list(questions.values())
        elif isinstance(questions, str):
            questions = [questions]
        if questions and isinstance(questions, list):
            lines.append(f"\n❓ QUESTIONS TO ASK YOURSELF:")
            for q in questions[:6]:
                lines.append(f"   • {_safe_str(q, max_len=200)}")

        # Warning signs / red flags - combine both VC and bootstrap red flags if available
        warnings = (
            framework.get("warning_signs") or
            framework.get("red_flags") or
            []
        )
        # Also check for specific red_flags_for_vc / red_flags_for_bootstrapping (various key names)
        vc_flags = framework.get("red_flags_for_vc", []) or framework.get("red_flags_for_vc_path", [])
        bootstrap_flags = framework.get("red_flags_for_bootstrapping", []) or framework.get("red_flags_for_bootstrap_path", [])
        if vc_flags or bootstrap_flags:
            warnings = []
            if vc_flags:
                warnings.extend([f"[VC path] {f}" for f in vc_flags[:2]])
            if bootstrap_flags:
                warnings.extend([f"[Bootstrap path] {f}" for f in bootstrap_flags[:2]])

        # Ensure it's a list
        if isinstance(warnings, dict):
            warnings = list(warnings.values())
        elif isinstance(warnings, str):
            warnings = [warnings]
        if warnings and isinstance(warnings, list):
            lines.append(f"\n⚠️ WARNING SIGNS:")
            for w in warnings[:5]:
                lines.append(f"   • {_safe_str(w, max_len=100)}")

    # Summary
    lines.append(f"\n" + "-" * 70)
    summary = report.get('summary') or report.get('conclusion')
    lines.append(f"📝 SUMMARY: {_safe_str(summary, max_len=1000)}")
    lines.append("-" * 70)

    return "\n".join(lines)
