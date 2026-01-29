"""
API routes for Counter-Narrative Generator
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
import json
import os
from datetime import datetime

from .schemas import (
    QueryRequest,
    QueryResponse,
    StatsResponse,
    TopicsResponse,
    HealthResponse,
    ErrorResponse,
    ProgressUpdate,
)
from src.config import config, TOPIC_TAXONOMY
from src.data.vectorstore import VectorStore
from services.workflow_service import WorkflowService

# Initialize router
router = APIRouter(prefix="/api", tags=["api"])

# Global state for vector store and workflow service
_vectorstore: Optional[VectorStore] = None
_workflow_service: Optional[WorkflowService] = None


def get_vectorstore() -> VectorStore:
    """Get or initialize the vector store"""
    global _vectorstore
    if _vectorstore is None:
        print(f"[INIT] Creating new VectorStore instance")
        _vectorstore = VectorStore()
        print(f"[INIT] VectorStore created, checking if loaded...")
        if not _vectorstore.is_loaded():
            print(f"[INIT] VectorStore is empty, loading chunks from {config.chunks_path}")
            try:
                count = _vectorstore.load_from_file(config.chunks_path)
                print(f"[INIT] ✅ Loaded {count:,} chunks into VectorStore")
            except Exception as e:
                print(f"[INIT] ❌ Error loading chunks: {e}")
                raise
        else:
            count = _vectorstore.collection.count()
            print(f"[INIT] ✅ VectorStore already loaded with {count:,} chunks")
    return _vectorstore


def get_workflow_service() -> WorkflowService:
    """Get or initialize the workflow service"""
    global _workflow_service
    if _workflow_service is None:
        vectorstore = get_vectorstore()
        _workflow_service = WorkflowService(vectorstore)
    return _workflow_service


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run"""
    api_key_configured = bool(config.models.api_key)

    try:
        vectorstore = get_vectorstore()
        vectorstore_loaded = vectorstore.is_loaded()
    except Exception:
        vectorstore_loaded = False

    return HealthResponse(
        status="healthy" if (api_key_configured and vectorstore_loaded) else "degraded",
        version="1.0.0",
        vectorstore_loaded=vectorstore_loaded,
        api_key_configured=api_key_configured,
    )


@router.get("/topics", response_model=TopicsResponse)
async def get_topics():
    """Get available topic filters"""
    return TopicsResponse(
        topics=list(TOPIC_TAXONOMY.keys()),
        taxonomy=TOPIC_TAXONOMY,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get vector store statistics"""
    try:
        vectorstore = get_vectorstore()

        if not vectorstore.is_loaded():
            raise HTTPException(status_code=503, detail="Vector store not loaded")

        stats = vectorstore.get_stats()

        return StatsResponse(
            total_chunks=stats.get("total_chunks", 0),
            collection_name=stats.get("collection_name", ""),
            topics=stats.get("topics", {}),
            sample_chunks=stats.get("sample_chunks", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_counter_narratives(request: QueryRequest):
    """
    Query for counter-narratives to a given belief

    This endpoint executes the three-agent workflow to find contrarian perspectives
    """
    try:
        # Validate API key
        if not config.models.api_key:
            raise HTTPException(
                status_code=401,
                detail="OPENROUTER_API_KEY not configured",
            )

        # Get workflow service
        workflow_service = get_workflow_service()

        # Execute workflow
        result = await workflow_service.run_workflow(
            conventional_wisdom=request.belief,
            filter_topics=request.topics,
            n_contrarian_results=request.n_results,
            user_context=request.user_context,
            verbose=request.verbose,
        )

        # Check if workflow was successful
        if not result.success:
            error_msg = "; ".join(result.errors) if result.errors else "Workflow failed"
            raise HTTPException(status_code=500, detail=error_msg)

        # Return formatted response
        return QueryResponse(
            conventional_wisdom=result.conventional_wisdom,
            topics_filter=result.topics_filter,
            forethought=result.forethought_output,
            quickaction=result.quickaction_output,
            examiner=result.examiner_output,
            metadata={
                "success": result.success,
                "total_tokens": result.total_tokens,
                "execution_time_ms": result.execution_time_ms,
                "errors": result.errors,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("[ERROR] /api/query failed:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.websocket("/query/stream")
async def query_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming query progress

    Clients should send a JSON message with the same format as QueryRequest
    """
    await websocket.accept()

    try:
        # Receive query request
        data = await websocket.receive_text()
        request_data = json.loads(data)

        # Validate request
        try:
            request = QueryRequest(**request_data)
        except Exception as e:
            error_update = ProgressUpdate(
                agent="system",
                status="error",
                message=f"Invalid request: {str(e)}",
                timestamp=datetime.utcnow().isoformat(),
            )
            await websocket.send_text(error_update.model_dump_json())
            await websocket.close()
            return

        # Validate API key
        if not config.models.api_key:
            error_update = ProgressUpdate(
                agent="system",
                status="error",
                message="OPENROUTER_API_KEY not configured",
                timestamp=datetime.utcnow().isoformat(),
            )
            await websocket.send_text(error_update.model_dump_json())
            await websocket.close()
            return

        # Progress callback
        async def send_progress(agent: str, status: str, message: str = None, data: dict = None):
            update = ProgressUpdate(
                agent=agent,
                status=status,
                message=message,
                data=data,
                timestamp=datetime.utcnow().isoformat(),
            )
            await websocket.send_text(update.model_dump_json())

        # Get workflow service
        workflow_service = get_workflow_service()

        # Execute workflow with progress callback
        result = await workflow_service.run_workflow(
            conventional_wisdom=request.belief,
            filter_topics=request.topics,
            n_contrarian_results=request.n_results,
            user_context=request.user_context,
            verbose=True,
            progress_callback=send_progress,
        )

        # Send final result
        if result.success:
            final_update = ProgressUpdate(
                agent="workflow",
                status="completed",
                message="Workflow completed successfully",
                data=result.to_dict(),
                timestamp=datetime.utcnow().isoformat(),
            )
            await websocket.send_text(final_update.model_dump_json())
        else:
            error_update = ProgressUpdate(
                agent="workflow",
                status="error",
                message="; ".join(result.errors) if result.errors else "Workflow failed",
                timestamp=datetime.utcnow().isoformat(),
            )
            await websocket.send_text(error_update.model_dump_json())

        await websocket.close()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            error_update = ProgressUpdate(
                agent="system",
                status="error",
                message=f"Unexpected error: {str(e)}",
                timestamp=datetime.utcnow().isoformat(),
            )
            await websocket.send_text(error_update.model_dump_json())
        except:
            pass
        await websocket.close()
