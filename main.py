"""
LlamaOrchestrator FastAPI Application
Exposes REST and Server-Sent Events (SSE) endpoints for multi-agent orchestration,
voice-driven Jarvis interaction, live DAG monitoring, and workspace downloads.
"""

import asyncio
import json
import re
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from core.browser_controller import BrowserController  # pyright: ignore[reportMissingImports]
from core.config import settings  # pyright: ignore[reportMissingImports]
from core.creator_memory import creator_memory  # pyright: ignore[reportMissingImports]
from core.mcp_server import MCPSandboxSecurityError  # pyright: ignore[reportMissingImports]
from core.models import (  # pyright: ignore[reportMissingImports]
    AnalyzeRequest,
    ChatRequest,
    ChatResponse,
    ExecutionEvent,
    ExportPathRequest,
    FolderUpdateRequest,
    ImportPathRequest,
    LaunchRequest,
    PinUpdateRequest,
)
from core.orchestrator import orchestrator  # pyright: ignore[reportMissingImports]
from core.scheduler import scheduler  # pyright: ignore[reportMissingImports]
from core.workflow_manager import history_manager  # pyright: ignore[reportMissingImports]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch 24/7 background scheduler loop
    scheduler_task = asyncio.create_task(scheduler.autonomous_scheduler_daemon(orchestrator, poll_interval_sec=25))
    yield
    # Shutdown: cancel task cleanly
    scheduler_task.cancel()

app = FastAPI(
    title="LlamaOrchestrator API",
    description="Autonomous Hierarchical Multi-Agent Engine & AI Partner for Meta Global AI Hackathon",
    version="1.0.0",
    lifespan=lifespan
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
            except TimeoutError:
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

@app.delete("/api/history/{session_id}")
async def delete_history_session(session_id: str):
    """Deletes a mission session from history and removes its workspace files."""
    deleted = history_manager.delete_session(session_id)
    try:
        ws_dir = (settings.WORKSPACE_DIR / session_id).resolve()
        if ws_dir.exists() and ws_dir.is_dir():
            shutil.rmtree(ws_dir, ignore_errors=True)
    except Exception:
        pass
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found in history")
    return {"success": True, "session_id": session_id}

@app.get("/api/workflows")
async def get_saved_workflows():
    """Returns saved workflow templates."""
    return history_manager.list_workflows()

@app.post("/api/workflows")
async def save_workflow_template(workflow: dict):
    """Saves a new workflow template."""
    history_manager.save_workflow(workflow)
    return {"success": True}

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow_template(workflow_id: str):
    """Deletes a saved workflow template."""
    deleted = history_manager.delete_workflow(workflow_id)
    return {"success": deleted}

@app.get("/api/schedules")
async def get_schedules():
    """Returns scheduled and recurring autonomous tasks."""
    return history_manager.list_schedules()

@app.post("/api/schedules")
async def add_schedule(task: dict):
    """Adds a new scheduled recurring task."""
    entry = history_manager.add_schedule(task)
    return {"success": True, "schedule": entry}

@app.post("/api/schedules/{task_id}/toggle")
async def toggle_schedule_active(task_id: str, req: dict = Body(...)):
    """Toggles active/paused status of a scheduled task."""
    is_active = bool(req.get("is_active", True))
    history_manager.toggle_schedule(task_id, is_active)
    return {"success": True, "is_active": is_active}

@app.post("/api/schedules/{task_id}/run-now")
async def trigger_schedule_now(task_id: str, background_tasks: BackgroundTasks):
    """Forces immediate background execution of a scheduled recurring mission."""
    schedules = history_manager.list_schedules()
    target = None
    for s in schedules:
        if s.get("task_id") == task_id or s.get("id") == task_id:
            target = s
            break
    if not target:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    background_tasks.add_task(
        orchestrator.run_scheduled_mission,
        prompt=target.get("prompt", ""),
        title=target.get("title", "Manual Scheduled Mission Trigger")
    )
    return {"success": True, "message": f"Execution initiated for '{target.get('title')}'"}

@app.delete("/api/schedules/{task_id}")
async def delete_schedule(task_id: str):
    """Deletes a scheduled task."""
    deleted = history_manager.delete_schedule(task_id)
    return {"success": deleted}

# ==========================================
# REAL BROWSER CONTROLLER & EMAIL DISPATCH
# ==========================================

@app.post("/api/browser/open")
async def browser_open_url(req: dict = Body(...)):
    """Opens a target URL in the user's host browser with their active logged-in sessions."""
    url = req.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' parameter")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    success = await asyncio.to_thread(BrowserController.open_in_system_browser, url)
    return {"success": success, "url": url}

@app.post("/api/browser/compose-email")
async def browser_compose_email(req: dict = Body(...)):
    """
    Opens the user's active host browser directly into Gmail Compose.
    If session_id is provided, extracts generated letters (mail_1.md, mail_2.md, mail_3.md).
    """
    recipient = req.get("recipient", "anshtiwarisocial@gmail.com")
    subject = req.get("subject", "hello i am jarvis")
    body = req.get("body")
    session_id = req.get("session_id")
    open_all = req.get("open_all", True)

    emails_to_open = []

    if session_id:
        ws_path = (settings.WORKSPACE_DIR / session_id).resolve()
        letters = ["mail_1.md", "mail_2.md", "mail_3.md"]
        found_any = False
        for l in letters:
            fpath = ws_path / l
            if fpath.exists():
                found_any = True
                content = fpath.read_text(encoding="utf-8", errors="replace")
                emails_to_open.append({
                    "to": recipient,
                    "subject": subject,
                    "body": content
                })
        if not found_any and body:
            emails_to_open.append({"to": recipient, "subject": subject, "body": body})
    elif body:
        emails_to_open.append({"to": recipient, "subject": subject, "body": body})
    else:
        # Default 3 letters if empty
        emails_to_open = [
            {"to": recipient, "subject": subject, "body": "Dear Ansh,\n\nI am your technical co-architect and loyal AI partner. All systems online.\n\n- Jarvis"},
            {"to": recipient, "subject": subject, "body": "Dear Ansh,\n\nStanding by for multi-agent autonomous execution whenever you command.\n\n- Jarvis"},
            {"to": recipient, "subject": subject, "body": "Dear Ansh,\n\nReady to conquer the Meta Global AI Hackathon with production-grade autonomous swarms.\n\n- Jarvis"}
        ]

    if not open_all and len(emails_to_open) > 1:
        emails_to_open = emails_to_open[:1]

    res = await asyncio.to_thread(BrowserController.compose_batch_in_gmail, emails_to_open)
    return res

@app.post("/api/browser/playwright-run")
async def browser_playwright_run(req: dict = Body(...)):
    """Executes a real Playwright browser session (Edge/Chrome) on the user's desktop."""
    recipient = req.get("recipient")
    subject = req.get("subject", "hello i am jarvis")
    body = req.get("body")
    session_id = req.get("session_id")
    headless = bool(req.get("headless", False))

    if session_id:
        ws_path = (settings.WORKSPACE_DIR / session_id).resolve()
        for candidate in ["mail_1.md", "letter_1.md", "email_1.md"]:
            f = ws_path / candidate
            if f.exists():
                body = f.read_text(encoding="utf-8", errors="replace")
                break

    if not body:
        body = "Hello Master Ansh, this is Jarvis executing autonomously like a real person on your desktop."

    if recipient:
        res = await BrowserController.automate_gmail_dispatch_playwright_async(
            recipient=recipient,
            subject=subject,
            body=body,
            headless=headless
        )
        return res

    url = req.get("url", "https://mail.google.com")
    actions = req.get("actions", [])
    res = await asyncio.to_thread(
        BrowserController.run_playwright_automation,
        url=url,
        headless=headless,
        actions=actions
    )
    return res

@app.post("/api/email/smtp-send")
async def email_smtp_send(req: dict = Body(...)):
    """Direct RFC-5322 SMTP transmission if credentials are provided in request or environment."""
    recipient = req.get("recipient", "anshtiwarisocial@gmail.com")
    subject = req.get("subject", "hello i am jarvis")
    body = req.get("body", "Hello from Jarvis.")
    sender = req.get("sender_email")
    pwd = req.get("password")
    smtp_server = req.get("smtp_server", "smtp.gmail.com")
    smtp_port = int(req.get("smtp_port", 587))

    res = await asyncio.to_thread(
        BrowserController.send_smtp_email,
        recipient=recipient,
        subject=subject,
        body=body,
        sender_email=sender,
        password=pwd,
        smtp_server=smtp_server,
        smtp_port=smtp_port
    )
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
