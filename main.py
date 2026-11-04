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

# Next.js export directory
FRONTEND_OUT = Path(__file__).resolve().parent / "frontend" / "out"
NEXT_STATIC = FRONTEND_OUT / "_next"
NEXT_STATIC.mkdir(parents=True, exist_ok=True)
app.mount("/_next", StaticFiles(directory=str(NEXT_STATIC)), name="next_assets")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serves the central dark-mode dashboard with zero-cache headers."""
    # Priority 1: Modern Next.js Command Center Export
    next_index = FRONTEND_OUT / "index.html"
    if next_index.exists():
        with open(next_index, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    # Priority 2: Static HTML
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

# ==========================================
# AGENT TELEMETRY & MULTI-AGENT SWARM METRICS
# ==========================================
@app.get("/api/agents/telemetry")
async def get_agents_telemetry():
    """Returns telemetry on synthesized autonomous sub-agents across sessions."""
    from core.workflow_manager import workflow_manager
    history = workflow_manager.list_history()
    latest_session_id = history[0].get("session_id") if history else None
    latest_sess = orchestrator.sessions.get(latest_session_id) if latest_session_id else None
    
    agents = []
    if latest_sess and latest_sess.agents_spawned:
        agents = latest_sess.agents_spawned
    elif history and history[0].get("agent_types"):
        agents = [{"id": f"agent_{i+1}", "title": role, "agent_type": role} for i, role in enumerate(history[0]["agent_types"])]
        
    total_cumulative = sum(h.get("agents_created", 0) for h in history)
    unique_roles = list(dict.fromkeys(a.get("agent_type", "") for a in agents if a.get("agent_type")))

    return {
        "status": "online",
        "latest_mission": history[0].get("title", "Standing by") if history else "Standing by",
        "latest_session_id": latest_session_id,
        "agents_created": len(agents) or (history[0].get("agents_created", 0) if history else 0),
        "unique_roles": unique_roles,
        "agents": agents,
        "total_cumulative_agents": total_cumulative or len(agents)
    }

# ==========================================
# VOICE TELEPHONY & INTERACTIVE ROLEPLAY HUB
# ==========================================
@app.get("/api/voice/telemetry")
async def get_voice_telemetry():
    from core.voice_call_agent import voice_call_engine
    doc = voice_call_engine.doctor()
    camps = voice_call_engine.list_campaigns()
    return {"health": doc, "campaigns": camps}

@app.post("/api/voice/roleplay")
async def voice_roleplay_turn(req: dict = Body(...)):
    """Executes a single conversational roleplay turn with Voss Tactical Empathy."""
    from core.voice_call_agent import voice_call_engine, VoiceCallLead, VoiceAgentPersona
    utterance = req.get("utterance", "").strip()
    history = req.get("history", [])
    niche = req.get("niche", "Autonomous Drone Delivery")
    lead_name = req.get("name", "Dr. Marcus Vance")
    lead_company = req.get("company", "Apex Healthcare")
    
    lead = VoiceCallLead(
        phone="+15550199201",
        name=lead_name,
        company=lead_company,
        niche=niche
    )
    persona = VoiceAgentPersona(
        agent_name="JARVIS",
        creator_name="Ansh Tiwari",
        calendly_link="https://calendly.com/anshtiwari"
    )
    reply = await voice_call_engine.generate_cognitive_call_reply(
        lead=lead,
        prospect_utterance=utterance,
        conversation_history=history,
        persona=persona
    )
    is_booked = any(w in reply.lower() for w in ["will see you thursday", "invite is on its way", "invite and prototype link are in your inbox", "booked"])
    return {
        "reply": reply,
        "is_booked": is_booked,
        "booking_slot": "Thursday 2:00 PM EST" if is_booked else None,
        "calendar_url": "https://calendly.com/anshtiwari"
    }

@app.post("/api/voice/campaign")
async def launch_voice_campaign(req: dict = Body(...)):
    from core.voice_call_agent import voice_call_engine
    niche = req.get("niche", "AI Automation & Custom Software")
    count = int(req.get("count", 10))
    price = int(req.get("price", 2500))
    res = await voice_call_engine.execute_cold_call_campaign(
        niche=niche,
        total_leads_count=count,
        offer_price=price,
        target_revenue=count * price // 2
    )
    return res

# ==========================================
# REA // REVERSE ENGINEERING ENGINE HUB
# ==========================================
@app.post("/api/rea/audit")
async def rea_audit_binary(req: dict = Body(...)):
    from core.rea_powerup import rea_engine
    target = req.get("target_path", "sample.exe")
    return rea_engine.audit_binary_security(target)

@app.post("/api/rea/inspect")
async def rea_inspect_binary(req: dict = Body(...)):
    from core.rea_powerup import rea_engine
    target = req.get("target_path", "sample.exe")
    return rea_engine.inspect_binary(target)

@app.post("/api/rea/secrets")
async def rea_scan_secrets(req: dict = Body(...)):
    from core.rea_powerup import rea_engine
    target = req.get("target_path", "sample.exe")
    return rea_engine.scan_secrets_and_keys(target)

# ==========================================
# HERMES // COGNITIVE SUPERCHARGER HUB
# ==========================================
@app.get("/api/hermes/skills")
async def list_hermes_skills(query: str | None = None):
    from core.hermes_powerup import hermes_skills
    skills = hermes_skills.list_skills(query)
    return {"total": len(skills), "skills": skills}

@app.get("/api/hermes/memory")
async def get_hermes_memory():
    from core.hermes_powerup import hermes_memory
    prof = hermes_memory.get_user_profile()
    return {"profile": prof}

@app.post("/api/hermes/learn")
async def create_hermes_skill(req: dict = Body(...)):
    from core.hermes_powerup import hermes_skills
    name = req.get("name", "custom_skill")
    desc = req.get("description", "Learned autonomous skill")
    instr = req.get("instructions", "Execution protocol")
    path = hermes_skills.create_skill(name, desc, instr)
    return {"success": True, "name": name, "path": str(path)}

# ==========================================
# RUNTIME TOOL SYNTHESIZER HUB
# ==========================================
@app.get("/api/tools/list")
async def list_synthesized_tools():
    from core.tool_synthesizer import tool_synthesizer
    manifest = tool_synthesizer.list_tools()
    return {"tools": manifest}

@app.post("/api/tools/synthesize")
async def synthesize_dynamic_tool(req: dict = Body(...)):
    from core.tool_synthesizer import tool_synthesizer
    name = req.get("name", "custom_tool")
    goal = req.get("goal", "Measure latency and log telemetry")
    res = tool_synthesizer.synthesize_tool_autonomously(name, goal)
    return res

# ==========================================
# BUILDS & WORKSPACES OPERATING HUB
# ==========================================
from core.build_manager import build_manager

@app.get("/api/builds")
async def list_jarvis_builds():
    """Returns all active, indexed builds and constructed systems across workspaces."""
    builds = build_manager.list_builds()
    return {"success": True, "count": len(builds), "builds": [b.to_dict() for b in builds]}

@app.get("/api/builds/{workspace_id:path}")
async def get_jarvis_build_info(workspace_id: str):
    """Returns detailed information and file breakdown for a specific build."""
    b = build_manager.get_build(workspace_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"Build '{workspace_id}' not found.")
    return {"success": True, "build": b.to_dict()}

@app.post("/api/builds/{workspace_id:path}/run")
async def run_jarvis_build(workspace_id: str, req: dict = Body(default_factory=dict)):
    """Executes a build in its sandboxed directory."""
    entrypoint = req.get("entrypoint")
    args = req.get("args")
    timeout = int(req.get("timeout_sec", 60))
    res = await asyncio.to_thread(build_manager.run_build, workspace_id, entrypoint, args, timeout)
    return res

@app.post("/api/builds/{workspace_id:path}/test")
async def test_jarvis_build(workspace_id: str):
    """Runs pytest unit tests for a specific build."""
    res = await asyncio.to_thread(build_manager.test_build, workspace_id)
    return res

@app.post("/api/builds/{workspace_id:path}/open")
async def open_jarvis_build_folder(workspace_id: str):
    """Opens the workspace directory in Windows File Explorer on the desktop."""
    res = await asyncio.to_thread(build_manager.open_in_explorer, workspace_id)
    return res

@app.post("/api/builds/clean")
async def clean_workspaces_endpoint(req: dict = Body(default_factory=dict)):
    """Safely prunes empty ghost directories and deduplicates test runs."""
    dry_run = bool(req.get("dry_run", False))
    res = await asyncio.to_thread(build_manager.clean_workspaces, True, True, dry_run)
    return res

# ==========================================
# Account Fleet & Cold Outreach Delivery Hub
# ==========================================
from core.account_fleet import account_fleet

@app.get("/api/fleet/summary")
async def get_fleet_summary(platform: str = "gmail"):
    """Returns real-time fleet health, total accounts, quota limits, and capacity."""
    return account_fleet.get_fleet_summary(platform=platform)

@app.post("/api/fleet/scale")
async def scale_fleet_topology_endpoint(req: dict = Body(default_factory=dict)):
    """Scales fleet to 20 or up to 200 accounts with safe daily quota limits."""
    count = int(req.get("target_count", 20))
    is_ws = bool(req.get("is_workspace", False))
    return account_fleet.scale_fleet_topology(target_account_count=count, is_workspace=is_ws)

@app.post("/api/fleet/verify")
async def verify_email_deliverability(req: dict = Body(default_factory=dict)):
    """Verifies physical email sendability via RFC syntax, disposable checks, and live DNS MX resolution."""
    email = req.get("email", "")
    if email:
        return account_fleet.validate_email_sendability(email)
    leads = req.get("leads", [])
    return account_fleet.filter_sendable_prospects(leads)

@app.get("/api/fleet/sequence")
async def get_outreach_sequence(niche: str = "Full-Stack Dev & AI Systems"):
    """Returns the 8-touch human-engineered email follow-up sequence."""
    return {"touches": account_fleet.generate_8_touch_sequence(company_niche=niche)}

@app.get("/api/fleet/notifications")
async def get_fleet_notifications():
    """Returns executive briefings of high-intent lead replies and Calendly meeting bookings."""
    return {"notifications": account_fleet.get_notifications()}

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

@app.post("/api/browser/agent/execute")
async def browser_agent_execute(req: dict = Body(...)):
    """
    Executes an autonomous goal using the dedicated Browser Agent.
    Interacts with live DOM, perceives numbered interactive elements ([#1], [#2]), and navigates on its own.
    """
    from core.browser_agent import browser_agent
    goal = req.get("goal", "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="Missing 'goal' parameter")
    start_url = req.get("start_url")
    max_steps = int(req.get("max_steps", 6))
    headless = bool(req.get("headless", False))

    res = await asyncio.to_thread(
        browser_agent.execute_goal,
        goal=goal,
        start_url=start_url,
        max_steps=max_steps,
        headless=headless
    )
    return res

@app.post("/api/browser/agent/email")
async def browser_agent_email(req: dict = Body(...)):
    """Specialized Browser Agent autonomous email dispatch with Host Browser session fallback."""
    from core.browser_agent import browser_agent
    recipient = req.get("recipient", "anshtiwarisocial@gmail.com")
    subject = req.get("subject", "hello i am jarvis")
    body = req.get("body", "I am writing this email as your autonomous technical partner.")

    res = await asyncio.to_thread(
        browser_agent.send_email_autonomously,
        recipient=recipient,
        subject=subject,
        body=body
    )
    return res

@app.post("/api/browser/login")
async def browser_login_portal(req: dict = Body(...)):
    """
    Launches visible persistent browser session for user to authenticate to any SaaS platform or service.
    Tokens & cookies are saved permanently in ~/.llama_orchestrator/browser_profile (Axiom Mode).
    """
    target = req.get("target") or req.get("service") or "google"
    browser = req.get("browser")
    res = await asyncio.to_thread(
        BrowserController.launch_login_session,
        target_url=target,
        preferred_browser=browser
    )
    return res

@app.post("/api/browser/leetcode")
async def browser_leetcode_solve(req: dict = Body(...)):
    """
    Autonomously navigates to LeetCode, extracts DOM problem stub, synthesizes polyglot algorithm,
    and submits directly to Monaco Editor.
    """
    from core.browser_agent import browser_agent
    slug = req.get("slug") or req.get("problem") or "daily"
    language = req.get("language")
    headless = req.get("headless", False)
    res = await asyncio.to_thread(
        browser_agent.solve_leetcode_problem,
        problem_slug_or_url=slug,
        language=language,
        headless=headless
    )
    return res

@app.post("/api/browser/browser-use")
async def browser_use_agent_task(req: dict = Body(...)):
    """
    Executes a high-level vision-action web browsing task using the browser-use engine
    powered by Groq (Meta Llama 3.3 70B) and persistent browser profile.
    """
    from core.browser_use_engine import browser_use_engine
    task = req.get("task", "").strip()
    if not task:
        raise HTTPException(status_code=400, detail="Missing 'task' parameter")
    max_steps = int(req.get("max_steps", 15))
    headless = bool(req.get("headless", False))
    return await browser_use_engine.execute_task(task=task, max_steps=max_steps, headless=headless)

if __name__ == "__main__":
    import uvicorn
    host_addr = settings.HOST if settings.HOST != "0.0.0.0" else "127.0.0.1"
    print("\n" + "=" * 75)
    print("   JARVIS // COGNITIVE MULTI-AGENT OS — WEB DASHBOARD")
    print("   Chief Systems Architect: Ansh Tiwari")
    print("=" * 75)
    print(f"  • Local Web Interface:  http://localhost:{settings.PORT}")
    print(f"  • Loopback Direct URL:   http://{host_addr}:{settings.PORT}")
    print("=" * 75 + "\n", flush=True)
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
