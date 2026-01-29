"""
API request/response schemas for Counter-Narrative Generator
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request for querying counter-narratives"""

    belief: str = Field(
        ...,
        description="The conventional wisdom or belief to challenge",
        min_length=10,
        max_length=500,
    )
    topics: Optional[List[str]] = Field(
        None,
        description="Optional list of topics to filter by",
    )
    n_results: Optional[int] = Field(
        5,
        description="Number of contrarian perspectives to find",
        ge=1,
        le=10,
    )
    user_context: Optional[str] = Field(
        None,
        description="Optional context about the user's situation",
        max_length=1000,
    )
    verbose: bool = Field(
        False,
        description="Enable verbose mode for detailed progress updates",
    )


class AgentOutput(BaseModel):
    """Output from a single agent"""

    data: Dict[str, Any]
    tokens: Optional[Dict[str, int]] = None


class QueryResponse(BaseModel):
    """Response from querying counter-narratives"""

    conventional_wisdom: str
    topics_filter: Optional[List[str]]
    forethought: Dict[str, Any] = Field(..., description="Contrarian findings from Forethought agent")
    quickaction: Dict[str, Any] = Field(..., description="Structured arguments from Quickaction agent")
    examiner: Dict[str, Any] = Field(..., description="Synthesis and analysis from Examiner agent")
    metadata: Dict[str, Any] = Field(..., description="Execution metadata (tokens, time, errors)")


class StatsResponse(BaseModel):
    """Vector store statistics"""

    total_chunks: int
    collection_name: str
    topics: Optional[Dict[str, int]] = None
    sample_chunks: Optional[List[Dict[str, Any]]] = None


class TopicsResponse(BaseModel):
    """Available topic filters"""

    topics: List[str]
    taxonomy: Dict[str, List[str]]


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    vectorstore_loaded: bool
    api_key_configured: bool


class ErrorResponse(BaseModel):
    """Error response"""

    error: str
    detail: Optional[str] = None
    status_code: int


class ProgressUpdate(BaseModel):
    """Progress update for streaming"""

    agent: str = Field(..., description="Current agent executing (forethought, quickaction, examiner)")
    status: str = Field(..., description="Status: started, in_progress, completed, error")
    message: Optional[str] = Field(None, description="Progress message")
    data: Optional[Dict[str, Any]] = Field(None, description="Partial or complete results")
    timestamp: str
