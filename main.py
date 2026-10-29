"""
LlamaOrchestrator FastAPI Application
Exposes REST and Server-Sent Events (SSE) endpoints for multi-agent orchestration,
voice-driven Jarvis interaction, live DAG monitoring, and workspace downloads.
"""

import json
import asyncio
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Body
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from core.config import settings  # pyright: ignore[reportMissingImports]
from core.mcp_server import MCPSandboxSecurityError  # pyright: ignore[reportMissingImports]
from core.models import (  # pyright: ignore[reportMissingImports]
    ChatRequest,
    ChatResponse,
    AnalyzeRequest,
    LaunchRequest,
    ExecutionEvent,
    FolderUpdateRequest,
    PinUpdateRequest,
    ImportPathRequest,
    ExportPathRequest
)
from core.creator_memory import creator_memory  # pyright: ignore[reportMissingImports]
from core.orchestrator import orchestrator, history_manager  # pyright: ignore[reportMissingImports]

app = FastAPI(
    title="LlamaOrchestrator API",
    description="Autonomous Hierarchical Multi-Agent Engine & AI Partner for Meta Global AI Hackathon",
    version="1.0.0"
)

# Enable CORS for cross-origin local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serves the central dark-mode dashboard with zero-cache headers."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>LlamaOrchestrator Dashboard Initializing...</h1>")
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/api/health")
async def health_check():
    """Returns engine health and LLM provider configuration status."""
    return {
        "status": "online",
        "system": settings.SYSTEM_NAME,
        "tagline": settings.SYSTEM_TAGLINE,
        "creator": settings.CREATOR_NAME,
        "mock_mode": settings.is_mock(),
        "orchestrator_model": settings.META_MODEL_ORCHESTRATOR,
        "worker_model": settings.META_MODEL_WORKER
    }

@app.post("/api/chat", response_model=ChatResponse)
async def central_brain_chat(req: ChatRequest):
    """Direct Jarvis/Alfred conversational interface recognizing Ansh Tiwari and judges."""
    llm = settings.get_llm_client()
    resp_dict = creator_memory.chat_response(
        user_message=req.message,
        is_mock=settings.is_mock(),
        llm_client=llm
    )
    return ChatResponse(**resp_dict)

@app.post("/api/analyze")
async def analyze_intent(req: AnalyzeRequest):
    """Stage 1: Ingests raw vision and returns Intent Analysis with clarification questions."""
    analysis = orchestrator.analyze_intent(vision=req.vision, session_id=req.session_id)
    return analysis.model_dump()

@app.post("/api/launch")
async def launch_lifecycle(req: LaunchRequest, background_tasks: BackgroundTasks):
    """Launches Stages 2 through 5 in the background, streaming progress via SSE."""
    session = orchestrator.get_or_create_session(req.session_id)
    if not session.intent_analysis:
        raise HTTPException(status_code=400, detail="Must execute /api/analyze prior to launch.")
    
    # Determine clarification answers
    if req.auto_approve or not req.answers:
        answers = session.intent_analysis.recommended_defaults
    else:
        answers = req.answers

    # Dispatch background execution
    background_tasks.add_task(
        orchestrator.execute_full_lifecycle,
        session_id=req.session_id,
        clarification_answers=answers
    )
    return {
        "success": True,
        "session_id": req.session_id,
        "message": "Autonomous multi-agent lifecycle initiated. Connect to /api/events/{session_id} for live telemetry."
    }

@app.get("/api/events/{session_id}")
async def sse_events(session_id: str, request: Request):
    """Server-Sent Events endpoint streaming real-time DAG logs and self-correction telemetry."""
    session = orchestrator.get_or_create_session(session_id)

    async def event_generator():
        # First send an initial connection ping
        init_evt = ExecutionEvent(
            event_type="log",
            session_id=session_id,
            stage=session.current_stage,
            stage_name="Telemetry Connected",
            message=f"Connected to LlamaOrchestrator telemetry stream for session '{session_id}'."
        )
        yield {
            "event": "message",
            "data": init_evt.model_dump_json()
        }

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            try:
                # Wait for next event with a periodic heartbeat
                evt: ExecutionEvent = await asyncio.wait_for(session.event_queue.get(), timeout=1.0)
                yield {
                    "event": "message",
                    "data": evt.model_dump_json()
                }
                session.event_queue.task_done()
                if evt.event_type == "done":
                    break
            except asyncio.TimeoutError:
                # Send periodic keep-alive comment
                yield {
                    "event": "ping",
                    "data": json.dumps({"timestamp": asyncio.get_event_loop().time()})
                }

    return EventSourceResponse(event_generator())

@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    """Retrieves current session state, artifacts, and evaluation report."""
    session = orchestrator.get_or_create_session(session_id)
    flist = session.mcp.tool_file_list()
    
    return {
        "session_id": session_id,
        "vision": session.vision,
        "current_stage": session.current_stage,
        "is_running": session.is_running,
        "is_completed": session.is_completed,
        "intent_analysis": session.intent_analysis.model_dump() if session.intent_analysis else None,
        "knowledge_base": session.knowledge_base.model_dump() if session.knowledge_base else None,
        "dag_plan": session.dag_plan.model_dump() if session.dag_plan else None,
        "evaluator_report": session.evaluator_report,
        "workspace_files": flist.get("files", [])
    }

@app.get("/api/workspace/{session_id}/download")
async def download_workspace(session_id: str):
    """1-Click ZIP export with Antigravity/Gemini human-readable session naming."""
    session = orchestrator.get_or_create_session(session_id)
    zip_bytes = orchestrator.create_zip_archive(session_id)
    
    # Antigravity/Gemini-style descriptive naming
    export_title = (session.dag_plan.title if (session.dag_plan and session.dag_plan.title) else getattr(session, "title", None)) or session_id
    clean_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', export_title).strip('_')
    clean_filename = re.sub(r'_+', '_', clean_filename)
    if not clean_filename:
        clean_filename = f"workspace_{session_id}"
        
    return StreamingResponse(
        zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={clean_filename}.zip"}
    )

@app.post("/api/workspace/{session_id}/import-path")
async def import_path_to_workspace(session_id: str, req: ImportPathRequest):
    """Safely imports an external host file or directory into the session workspace sandbox."""
    session = orchestrator.get_or_create_session(session_id)
    res = session.mcp.tool_import_external_path(source_path=req.source_path, target_name=req.target_name)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to import external path"))
    return res

@app.post("/api/workspace/{session_id}/export-to-path")
async def export_workspace_to_host(session_id: str, req: ExportPathRequest = Body(default_factory=ExportPathRequest)):
    """Exports session workspace deliverables directly to user's host Downloads with Antigravity/Gemini-style naming."""
    session = orchestrator.get_or_create_session(session_id)
    dest = req.destination_path if req and req.destination_path else None
    export_title = getattr(session, "title", None) or (session.dag_plan.title if session.dag_plan else None)
    res = session.mcp.tool_export_to_host(destination_path=dest, export_folder_name=export_title)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to export workspace"))
    return res

@app.get("/api/knowledge-base/{session_id}")
async def get_knowledge_base(session_id: str):
    """Fetches the session Knowledge Base."""
    session = orchestrator.get_or_create_session(session_id)
    if not session.knowledge_base:
        raise HTTPException(status_code=404, detail="Knowledge base not yet generated.")
    return session.knowledge_base.model_dump()

@app.post("/api/mock-booking")
async def receive_booking_webhook(payload: dict):
    """Simulated calendar webhook endpoint for client discovery call hand-offs."""
    return {
        "status": "received",
        "timestamp": asyncio.get_event_loop().time(),
        "client": payload.get("lead", {}).get("name", "Unknown Lead"),
        "confirmation": "Added to Ansh Tiwari's Primary Calendar"
    }

@app.get("/api/workspace/{session_id}/file")
async def get_workspace_file(session_id: str, path: str):
    """Reads a file from the workspace sandbox for in-browser preview."""
    session = orchestrator.get_or_create_session(session_id)
    try:
        res = session.mcp.tool_file_read(path)
        if not res.get("success"):
            raise HTTPException(status_code=404, detail=res.get("error", "File not found"))
        return res
    except MCPSandboxSecurityError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/api/history")
async def get_work_history():
    """Returns persistent searchable work history."""
    return history_manager.list_history()

@app.post("/api/history/folder")
async def update_history_folder(req: FolderUpdateRequest):
    """Updates folder categorization for a session."""
    history_manager.update_folder(req.session_id, req.folder)
    return {"success": True}

@app.post("/api/history/pin")
async def update_history_pin(req: PinUpdateRequest):
    """Toggles pin status for a session."""
    history_manager.toggle_pin(req.session_id, req.is_pinned)
    return {"success": True}

@app.get("/api/workflows")
async def get_saved_workflows():
    """Returns saved workflow templates."""
    return history_manager.list_workflows()

@app.post("/api/workflows")
async def save_workflow_template(workflow: dict):
    """Saves a new workflow template."""
    history_manager.save_workflow(workflow)
    return {"success": True}

@app.get("/api/schedules")
async def get_schedules():
    """Returns scheduled and recurring autonomous tasks."""
    return history_manager.list_schedules()

@app.post("/api/schedules")
async def add_schedule(task: dict):
    """Adds a new scheduled recurring task."""
    history_manager.add_schedule(task)
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
