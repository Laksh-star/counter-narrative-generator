"""
Workflow Service

Wraps the Counter-Narrative workflow with progress callbacks for streaming updates
"""

from typing import Optional, List, Callable, Awaitable, Any, Dict
import asyncio
from datetime import datetime

from src.workflow import CounterNarrativeWorkflow, WorkflowResult
from src.data.vectorstore import VectorStore


class WorkflowService:
    """
    Service wrapper for the Counter-Narrative workflow

    Adds support for progress callbacks to enable streaming updates via WebSocket
    """

    def __init__(self, vectorstore: VectorStore):
        """
        Initialize the workflow service

        Args:
            vectorstore: Loaded VectorStore with podcast chunks
        """
        self.vectorstore = vectorstore
        self.workflow = CounterNarrativeWorkflow(vectorstore)

    async def run_workflow(
        self,
        conventional_wisdom: str,
        filter_topics: Optional[List[str]] = None,
        n_contrarian_results: int = 5,
        user_context: Optional[str] = None,
        verbose: bool = False,
        progress_callback: Optional[Callable[[str, str, Optional[str], Optional[Dict]], Awaitable[None]]] = None,
    ) -> WorkflowResult:
        """
        Execute the Counter-Narrative workflow with optional progress streaming

        Args:
            conventional_wisdom: The belief to find contrarian views on
            filter_topics: Optional topics to filter by
            n_contrarian_results: How many contrarian perspectives to find
            user_context: Optional context about the user's situation
            verbose: Enable verbose logging
            progress_callback: Optional async callback function for progress updates
                              Signature: (agent: str, status: str, message: str, data: dict) -> None

        Returns:
            WorkflowResult with outputs from all three agents
        """
        # If no progress callback, run workflow directly in thread pool
        if not progress_callback:
            return await asyncio.to_thread(
                self.workflow.run,
                conventional_wisdom=conventional_wisdom,
                filter_topics=filter_topics,
                n_contrarian_results=n_contrarian_results,
                user_context=user_context,
                verbose=verbose,
            )

        # Run workflow with progress updates
        return await self._run_workflow_with_progress(
            conventional_wisdom=conventional_wisdom,
            filter_topics=filter_topics,
            n_contrarian_results=n_contrarian_results,
            user_context=user_context,
            verbose=verbose,
            progress_callback=progress_callback,
        )

    async def _run_workflow_with_progress(
        self,
        conventional_wisdom: str,
        filter_topics: Optional[List[str]],
        n_contrarian_results: int,
        user_context: Optional[str],
        verbose: bool,
        progress_callback: Callable[[str, str, Optional[str], Optional[Dict]], Awaitable[None]],
    ) -> WorkflowResult:
        """
        Run workflow in async context with progress updates

        This method sends progress updates for each agent execution
        """
        start_time = datetime.now()

        try:
            def _normalize_forethought(data: Any) -> Dict[str, Any]:
                """Normalize forethought output to expected dict format."""
                if isinstance(data, list):
                    return {
                        "conventional_wisdom": conventional_wisdom,
                        "contrarian_findings": data,
                    }
                if not isinstance(data, dict):
                    return {
                        "conventional_wisdom": conventional_wisdom,
                        "contrarian_findings": [],
                    }

                findings = (
                    data.get("contrarian_findings")
                    or data.get("contrarian_perspectives")
                    or data.get("findings")
                    or []
                )
                data["contrarian_findings"] = findings
                if "conventional_wisdom" not in data:
                    data["conventional_wisdom"] = conventional_wisdom
                return data

            # Notify workflow start
            await progress_callback(
                "workflow",
                "started",
                f"Starting Counter-Narrative workflow for: {conventional_wisdom[:100]}...",
                None,
            )

            # Step 1: Forethought Agent
            await progress_callback(
                "forethought",
                "started",
                "Searching for contrarian perspectives...",
                None,
            )

            # Execute Forethought
            forethought_result = await asyncio.to_thread(
                self.workflow.forethought.run,
                conventional_wisdom,
                filter_topics,
                n_contrarian_results,
            )

            # Debug logging
            import json
            print(f"[DEBUG] Forethought result data type: {type(forethought_result.data)}")
            print(f"[DEBUG] Forethought result data keys: {forethought_result.data.keys() if isinstance(forethought_result.data, dict) else 'not a dict'}")
            print(f"[DEBUG] Forethought result data: {json.dumps(forethought_result.data, indent=2)[:1000]}")

            # Get findings count
            normalized_forethought = _normalize_forethought(forethought_result.data)
            findings = normalized_forethought.get("contrarian_findings", [])

            print(f"[DEBUG] Extracted findings count: {len(findings)}")
            if findings:
                print(f"[DEBUG] First finding keys: {findings[0].keys() if isinstance(findings[0], dict) else 'not a dict'}")
                print(f"[DEBUG] First finding: {json.dumps(findings[0], indent=2)[:500]}")

            await progress_callback(
                "forethought",
                "completed",
                f"Found {len(findings)} contrarian perspectives",
                {"findings_count": len(findings)},
            )

            # Check if we have findings before continuing
            if not findings:
                print("[DEBUG] No contrarian perspectives found, stopping workflow")
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                return WorkflowResult(
                    conventional_wisdom=conventional_wisdom,
                    topics_filter=filter_topics,
                    forethought_output=normalized_forethought,
                    quickaction_output={},
                    examiner_output={},
                    success=False,
                    total_tokens={
                        "prompt": forethought_result.usage.get("prompt_tokens", 0),
                        "completion": forethought_result.usage.get("completion_tokens", 0),
                        "total": forethought_result.usage.get("total_tokens", 0),
                    },
                    execution_time_ms=execution_time,
                    errors=["No contrarian perspectives found in podcast data"],
                )

            # Step 2: Quickaction Agent
            await progress_callback(
                "quickaction",
                "started",
                "Structuring arguments and identifying themes...",
                None,
            )

            # Execute Quickaction with normalized data
            quickaction_result = await asyncio.to_thread(
                self.workflow.quickaction.run,
                normalized_forethought,
            )

            # Get arguments count
            if isinstance(quickaction_result.data, dict):
                arguments = quickaction_result.data.get('structured_arguments', [])
            else:
                arguments = quickaction_result.data if isinstance(quickaction_result.data, list) else []

            await progress_callback(
                "quickaction",
                "completed",
                f"Structured {len(arguments)} arguments",
                {"arguments_count": len(arguments)},
            )

            # Step 3: Examiner Agent
            await progress_callback(
                "examiner",
                "started",
                "Synthesizing debate and creating decision framework...",
                None,
            )

            # Execute Examiner
            examiner_result = await asyncio.to_thread(
                self.workflow.examiner.run,
                quickaction_result.data,
                user_context,
            )

            await progress_callback(
                "examiner",
                "completed",
                "Analysis complete",
                None,
            )

            # Calculate total tokens and execution time
            total_tokens = {
                "prompt": (
                    forethought_result.usage.get("prompt_tokens", 0)
                    + quickaction_result.usage.get("prompt_tokens", 0)
                    + examiner_result.usage.get("prompt_tokens", 0)
                ),
                "completion": (
                    forethought_result.usage.get("completion_tokens", 0)
                    + quickaction_result.usage.get("completion_tokens", 0)
                    + examiner_result.usage.get("completion_tokens", 0)
                ),
                "total": (
                    forethought_result.usage.get("total_tokens", 0)
                    + quickaction_result.usage.get("total_tokens", 0)
                    + examiner_result.usage.get("total_tokens", 0)
                ),
            }

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Create result
            result = WorkflowResult(
                conventional_wisdom=conventional_wisdom,
                topics_filter=filter_topics,
                forethought_output=normalized_forethought,
                quickaction_output=quickaction_result.data,
                examiner_output=examiner_result.data,
                success=True,
                total_tokens=total_tokens,
                execution_time_ms=execution_time,
                errors=[],
            )

            return result

        except Exception as e:
            # Handle errors
            await progress_callback(
                "workflow",
                "error",
                f"Error executing workflow: {str(e)}",
                None,
            )

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return WorkflowResult(
                conventional_wisdom=conventional_wisdom,
                topics_filter=filter_topics,
                forethought_output={},
                quickaction_output={},
                examiner_output={},
                success=False,
                total_tokens={"prompt": 0, "completion": 0, "total": 0},
                execution_time_ms=execution_time,
                errors=[str(e)],
            )
