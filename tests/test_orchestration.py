"""
Comprehensive Test Suite for LlamaOrchestrator
Tests all 6 lifecycle stages, MCP sandboxing security, DAG compilation,
and FastAPI REST & SSE endpoints.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.creator_memory import CreatorMemory  # pyright: ignore[reportMissingImports]
from core.evaluator import EvaluatorGatekeeper  # pyright: ignore[reportMissingImports]
from core.knowledge_agent import KnowledgeAgent  # pyright: ignore[reportMissingImports]
from core.mcp_server import MCPSandboxSecurityError, MCPServer  # pyright: ignore[reportMissingImports]
from core.models import SubAgentSpec, TaskNode  # pyright: ignore[reportMissingImports]
from core.orchestrator import MetaOrchestrator  # pyright: ignore[reportMissingImports]
from core.worker import DynamicWorkerEngine, clean_code_content  # pyright: ignore[reportMissingImports]
from main import app  # pyright: ignore[reportMissingImports]


@pytest.fixture
def temp_workspace():
    temp_dir = Path(tempfile.mkdtemp(prefix="llama_orch_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_creator_memory(temp_workspace):
    """Test Stage 0: Jarvis Central Brain Creator recognition for Ansh Tiwari."""
    mem_file = temp_workspace / "test_memory.json"
    mem = CreatorMemory(memory_path=mem_file)
    
    assert mem.data["creator_name"] == "Ansh Tiwari"
    assert "Jarvis" in mem.data["persona"]
    
    # Test judge introduction
    intro = mem.get_judge_introduction()
    assert "Meta Hackathon" in intro
    assert "Ansh Tiwari" in intro
    assert "LlamaOrchestrator" in intro
    
    # Test chat response recognition
    resp = mem.chat_response("Hello Jarvis, what is your status?", is_mock=True)
    assert "Ansh" in resp["text"]
    assert resp["speaker"] == "LlamaOrchestrator (Central Brain)"

def test_mcp_sandboxing_and_path_containment(temp_workspace):
    """Test Stage 4: MCP Sandboxed Tool Server and security path containment."""
    mcp = MCPServer(temp_workspace)
    
    # 1. Normal safe file write & read
    write_res = mcp.tool_file_write("subfolder/test_artifact.txt", "Autonomous Agent Output")
    assert write_res["success"] is True
    assert (temp_workspace / "subfolder" / "test_artifact.txt").exists()
    
    read_res = mcp.tool_file_read("subfolder/test_artifact.txt")
    assert read_res["success"] is True
    assert read_res["content"] == "Autonomous Agent Output"
    
    # 2. File listing
    flist = mcp.tool_file_list()
    assert flist["success"] is True
    assert len(flist["files"]) >= 1
    
    # 3. Path Traversal Attack Security Check!
    with pytest.raises(MCPSandboxSecurityError):
        mcp.tool_file_write("../../forbidden_host_escape.txt", "Malicious Escape Attempt")
        
    with pytest.raises(MCPSandboxSecurityError):
        mcp.tool_file_read("../../../windows/system.ini")

    # 4. Email syntax validator
    valid_res = mcp.tool_verify_email_syntax("sarah.chen@synthetica.ai")
    assert valid_res["valid"] is True
    invalid_res = mcp.tool_verify_email_syntax("invalid-email-no-at")
    assert invalid_res["valid"] is False

    # 5. Command execution
    cmd_res = mcp.tool_run_command("python -c \"print('MCP Subprocess OK')\"")
    assert cmd_res["success"] is True, f"Command failed: {cmd_res}"
    assert "MCP Subprocess OK" in cmd_res["stdout"]

    # 6. Browser and UI automation tools
    interact_res = mcp.tool_browser_interact(action="click", target="#submit-solution-btn")
    assert interact_res["success"] is True
    assert "Executed UI action" in interact_res["status"]

    tool_defs = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in tool_defs]
    assert "browser_navigate" in tool_names
    assert "browser_screenshot" in tool_names
    assert "browser_interact" in tool_names

def test_intent_analysis_stage_1():
    """Test Stage 1: Intent Analysis & Human Clarification Gate."""
    orch = MetaOrchestrator()
    
    # Business Track Vision
    biz_analysis = orch.analyze_intent("I know full-stack dev, build me a business and find me clients")
    assert bool(biz_analysis.track_type)
    assert len(biz_analysis.clarifications) >= 1
    assert len(biz_analysis.recommended_defaults) >= 1
    
    # Technical Track Vision
    tech_analysis = orch.analyze_intent("Build an authenticated telemetry microservice with JWT & tests")
    assert bool(tech_analysis.track_type)
    assert len(tech_analysis.clarifications) >= 1
    assert len(tech_analysis.recommended_defaults) >= 1

@pytest.mark.asyncio
async def test_knowledge_gathering_stage_2(temp_workspace):
    """Test Stage 2: Autonomous Knowledge Base Synthesis."""
    mcp = MCPServer(temp_workspace)
    agent = KnowledgeAgent()
    
    events = []
    async def capture_event(e):
        events.append(e)
        
    kb = await agent.gather_and_synthesize(
        session_id="test_sess_01",
        track_type="business_acquisition",
        vision="Build client acquisition business",
        clarification_answers={"target_niche": "Seed & Series A AI Startups"},
        mcp=mcp,
        emit_event=capture_event
    )
    
    assert kb.session_id == "test_sess_01"
    assert (temp_workspace / "knowledge_base.json").exists()
    assert len(kb.pricing_tiers) >= 1
    assert len(events) >= 1

def test_dag_compilation_stage_3(temp_workspace):
    """Test Stage 3: DAG Task Decomposition & Dynamic Worker Synthesis."""
    orch = MetaOrchestrator()
    session = orch.get_or_create_session("dag_test_sess", "build telemetry microservice")
    orch.analyze_intent("build telemetry microservice", session_id="dag_test_sess")
    
    dag = orch.compile_dag_and_synthesize_workers(session)
    assert len(dag.nodes) >= 3
    
    # Verify dynamic sub-agent spec synthesis
    for node in dag.nodes:
        assert node.title
        assert node.agent_type
        spec = orch.get_subagent_spec(node.agent_type, session)
        assert spec is not None
        assert len(spec.allowed_tools) >= 1

@pytest.mark.asyncio
async def test_worker_execution_and_evaluator_stage_4_5(temp_workspace):
    """Test Stages 4 & 5: Worker execution, sandboxed Pytest verification, and Evaluator certification."""
    mcp = MCPServer(temp_workspace)
    worker_engine = DynamicWorkerEngine(mcp=mcp)
    
    # Execute backend task
    task_backend = TaskNode(
        id="task_tech_backend_api",
        title="FastAPI Telemetry Microservice",
        agent_type="BackendAgent",
        description="Write telemetry microservice",
        assigned_tools=["file_write"]
    )
    spec_backend = SubAgentSpec(
        agent_id="a1", name="BackendAgent", role="Engineer", system_prompt="", allowed_tools=["file_write"]
    )
    success = await worker_engine.execute_task(task_backend, spec_backend, track_type="technical_software")
    assert success is True
    assert (temp_workspace / "telemetry_service.py").exists()

    # Execute test suite task
    task_test = TaskNode(
        id="task_tech_test_suite",
        title="Unit & Integration Tests",
        agent_type="TestAgent",
        description="Write and run pytest",
        assigned_tools=["run_command", "file_write"]
    )
    spec_test = SubAgentSpec(
        agent_id="a2", name="TestAgent", role="QA", system_prompt="", allowed_tools=["run_command", "file_write"]
    )
    test_success = await worker_engine.execute_task(task_test, spec_test, track_type="technical_software")
    assert test_success is True, f"Worker test failed: {task_test.execution_logs}"
    assert (temp_workspace / "test_telemetry.py").exists()

    # Stage 5: Evaluator Gatekeeper
    evaluator = EvaluatorGatekeeper(mcp=mcp)
    report = await evaluator.evaluate_deliverables("test_sess_02", track_type="technical_software")
    assert report["passed"] is True
    assert report["score_percentage"] == 100.0
    assert (temp_workspace / "evaluator_report.json").exists()

def test_fastapi_rest_endpoints():
    """Test FastAPI application endpoints."""
    client = TestClient(app)
    
    # 1. Health endpoint
    h_res = client.get("/api/health")
    assert h_res.status_code == 200
    assert h_res.json()["system"] == "LlamaOrchestrator"
    assert h_res.json()["creator"] == "Ansh Tiwari"
    
    # 2. Jarvis Chat
    c_res = client.post("/api/chat", json={"message": "Status report"})
    assert c_res.status_code == 200
    assert "LlamaOrchestrator" in c_res.json()["speaker"]
    assert "speech_audio" in c_res.json()
    
    # 3. Intent Analysis
    a_res = client.post("/api/analyze", json={"vision": "Build a client acquisition business"})
    assert a_res.status_code == 200
    sess_id = a_res.json()["session_id"]
    assert len(a_res.json()["clarifications"]) >= 1
    
    # 4. Session details
    s_res = client.get(f"/api/session/{sess_id}")
    assert s_res.status_code == 200
    assert s_res.json()["session_id"] == sess_id

    # 5. 1-Click ZIP Download
    d_res = client.get(f"/api/workspace/{sess_id}/download")
    assert d_res.status_code == 200
    assert d_res.headers["content-type"] == "application/zip"

    # 6. Path traversal security gate (returns 403 Forbidden)
    sec_res = client.get(f"/api/workspace/{sess_id}/file?path=../../sensitive.txt")
    assert sec_res.status_code == 403

def test_clean_code_content_and_url_normalization(temp_workspace):
    """Test code fence sanitization and URL schema auto-prefixing."""
    # 1. Test clean_code_content
    wrapped_py = "```python\ndef calculate(x: int) -> int:\n    return x * 2\n```"
    cleaned = clean_code_content("math_service.py", wrapped_py)
    assert cleaned == "def calculate(x: int) -> int:\n    return x * 2"
    assert not cleaned.startswith("```")
    assert not cleaned.endswith("```")

    raw_json = "```json\n{\"status\": \"ok\"}\n```"
    cleaned_json = clean_code_content("payload.json", raw_json)
    assert cleaned_json == "{\"status\": \"ok\"}"

    # 2. Test MCP tool_browser_navigate URL normalization
    mcp = MCPServer(temp_workspace)
    # Target bare domain without http:// prefix
    res = mcp.tool_browser_navigate("example.com", timeout_sec=5)
    assert res["success"] is True
    assert res["url"] == "https://example.com"

@pytest.mark.asyncio
async def test_omnichannel_campaign_and_ready_for_permission_queue(temp_workspace):
    """Test Omnichannel campaign synthesis, dedicated campaigns/ folder, and ready-to-authorize queue."""
    mcp = MCPServer(temp_workspace)
    worker_engine = DynamicWorkerEngine(mcp=mcp)

    task_campaign = TaskNode(
        id="task_biz_omnichannel_campaigns",
        title="Omnichannel Campaign Directory & Ready-to-Authorize Action Queue",
        agent_type="OmnichannelCampaignAgent",
        description="Compile campaigns/ directory",
        assigned_tools=["file_write", "file_read"]
    )
    spec_campaign = SubAgentSpec(
        agent_id="a_omni",
        name="OmnichannelCampaignAgent",
        role="Omnichannel Specialist",
        system_prompt="",
        allowed_tools=["file_write", "file_read"]
    )
    success = await worker_engine.execute_task(task_campaign, spec_campaign, track_type="business_acquisition")
    assert success is True

    # 1. Verify dedicated campaign folder artifacts exist
    assert (temp_workspace / "campaigns" / "linkedin" / "connection_notes.md").exists()
    assert (temp_workspace / "campaigns" / "linkedin" / "linkedin_browser_script.py").exists()
    assert (temp_workspace / "campaigns" / "communities" / "target_groups.json").exists()
    assert (temp_workspace / "campaigns" / "communities" / "high_value_posts.md").exists()
    assert (temp_workspace / "campaigns" / "twitter_x" / "dm_pitches.md").exists()
    assert (temp_workspace / "campaigns" / "cold_email" / "sequences.md").exists()
    assert (temp_workspace / "campaigns" / "ready_for_permission.json").exists()

    # 2. Verify ready_for_permission.json content integrity
    read_res = mcp.tool_file_read("campaigns/ready_for_permission.json")
    assert read_res["success"] is True
    import json
    q_data = json.loads(read_res["content"])
    assert q_data["status"] == "ready_for_permission"
    assert q_data["staging_mode"] == "non_blocking"
    assert len(q_data["actions"]) >= 4

    # 3. Verify Python syntax of linkedin_browser_script.py
    read_script = mcp.tool_file_read("campaigns/linkedin/linkedin_browser_script.py")
    assert "class LinkedInBrowserAutomator" in read_script["content"]
    syn = mcp.tool_run_command("python -m py_compile campaigns/linkedin/linkedin_browser_script.py")
    assert syn.get("returncode") == 0

@pytest.mark.asyncio
async def test_quantitative_trading_lifecycle(temp_workspace):
    """Test Universal Quantitative Trading Domain & sandboxed pytest verification."""
    orch = MetaOrchestrator()
    session = orch.get_or_create_session("test_quant_sess", "build algorithmic trading strategy for crypto and equities with risk limits")
    
    # 1. Intent Analysis
    analysis = orch.analyze_intent("build algorithmic trading strategy for crypto and equities with risk limits", session_id="test_quant_sess")
    assert analysis.track_type == "quantitative_trading"
    assert analysis.combat_tier in ["swarm_army", "tactical_squad"]
    assert len(analysis.clarifications) >= 1

    # 2. DAG Compilation
    dag = orch.compile_dag_and_synthesize_workers(session)
    assert len(dag.nodes) >= 3
    for node in dag.nodes:
        assert node.title
        assert node.agent_type
        spec = orch.get_subagent_spec(node.agent_type, session)
        assert spec is not None

    # 3. Worker Execution across quantitative trading modules
    mcp = MCPServer(temp_workspace)
    worker = DynamicWorkerEngine(mcp=mcp)
    quant_nodes = [
        TaskNode(id="task_quant_strategy", title="Strategy Alpha", agent_type="QuantStrategyAgent", description="Alpha"),
        TaskNode(id="task_quant_risk", title="Risk Manager", agent_type="RiskManagerAgent", description="Risk"),
        TaskNode(id="task_quant_backtest", title="Backtest Engine", agent_type="BacktestEngineAgent", description="Backtest"),
        TaskNode(id="task_quant_execution", title="Paper Execution", agent_type="PaperExecutionAgent", description="Execution"),
        TaskNode(id="task_quant_test", title="Quant Test", agent_type="QuantTestAgent", description="Tests")
    ]
    for qn in quant_nodes:
        spec = orch.get_subagent_spec(qn.agent_type, session)
        task_ok = await worker.execute_task(qn, spec, track_type="quantitative_trading")
        assert task_ok is True, f"Failed on {qn.id}: {qn.execution_logs}"

    # Verify trading artifacts exist
    assert (temp_workspace / "trading_strategy.py").exists()
    assert (temp_workspace / "risk_manager.py").exists()
    assert (temp_workspace / "backtest_engine.py").exists()
    assert (temp_workspace / "paper_execution_loop.py").exists()
    assert (temp_workspace / "test_trading_system.py").exists()
    assert (temp_workspace / "campaigns" / "ready_for_permission.json").exists()

    # 4. Evaluator Gatekeeper Certification
    evaluator = EvaluatorGatekeeper(mcp=mcp)
    report = await evaluator.evaluate_deliverables("test_quant_sess", track_type="quantitative_trading")
    assert report["passed"] is True
    assert report["score_percentage"] == 100.0

def test_autonomous_response_escalation():
    """Test Autonomous Escalation: solo direct response vs swarm army deployment."""
    orch = MetaOrchestrator()

    # Simple informational query
    query_analysis = orch.analyze_intent("what is the architecture of LlamaOrchestrator")
    assert query_analysis.response_mode == "direct_response"
    assert query_analysis.combat_tier == "solo"
    assert len(query_analysis.clarifications) == 0

    # Actionable building directive
    action_analysis = orch.analyze_intent("launch an omnichannel marketing and client acquisition agency")
    assert action_analysis.response_mode == "swarm_army"
    assert action_analysis.combat_tier in ["tactical_squad", "swarm_army"]


def test_host_file_ingestion_and_browser_tools(temp_workspace, tmp_path):
    """Verifies host file ingestion, host export, and advanced browser automation tools."""
    mcp = MCPServer(workspace_path=temp_workspace)

    # 1. Host File Ingestion
    host_file = tmp_path / "external_leads.csv"
    host_file.write_text("name,email,company\nAlice,alice@example.com,Acme Corp", encoding="utf-8")

    import_res = mcp.tool_import_external_path(str(host_file), target_name="imported_leads.csv")
    assert import_res["success"] is True
    assert (temp_workspace / "imported_leads.csv").exists()
    assert "Acme Corp" in (temp_workspace / "imported_leads.csv").read_text(encoding="utf-8")

    # 2. Host File Read
    read_ext = mcp.tool_read_external_path(str(host_file))
    assert read_ext["success"] is True
    assert "Alice" in read_ext["content"]

    # 3. Host Export
    export_dest = tmp_path / "host_downloads"
    export_res = mcp.tool_export_to_host(destination_path=str(export_dest))
    assert export_res["success"] is True
    # Export creates a subfolder named llama_export_<workspace_name> inside destination
    export_dir = Path(export_res["destination"])
    assert (export_dir / "imported_leads.csv").exists()

    # 4. Browser Automation Tools
    click_res = mcp.tool_browser_click(selector="#login-btn")
    assert click_res["success"] is True
    assert click_res["action"] == "click"

    type_res = mcp.tool_browser_type(selector="input[name='search']", text="CEO Founders", delay_ms=20)
    assert type_res["success"] is True
    assert type_res["text_length"] == 12

    # Browser DOM text extraction
    mock_dom = temp_workspace / "ui_snapshot.html"
    mock_dom.write_text("<html><body><h1>Dashboard</h1><a href='https://example.com/item'>Link</a><input name='lead_email'/></body></html>", encoding="utf-8")
    extract_res = mcp.tool_browser_extract_text()
    assert extract_res["success"] is True
    assert "Dashboard" in extract_res["text_snippet"]
    assert "https://example.com/item" in extract_res["extracted_links"]
    assert "lead_email" in extract_res["form_inputs"]


def test_import_export_fastapi_endpoints(tmp_path):
    """Verifies REST endpoints for importing external host paths and exporting to host."""
    client = TestClient(app)
    sess_id = "test_rest_io"
    client.post("/api/analyze", json={"vision": "build a quick service", "session_id": sess_id})

    # Prepare external file
    external_doc = tmp_path / "directive_brief.txt"
    external_doc.write_text("Launch campaign for Q4 target market.", encoding="utf-8")

    # Test Import Endpoint
    resp_import = client.post(
        f"/api/workspace/{sess_id}/import-path",
        json={"source_path": str(external_doc), "target_name": "brief.txt"}
    )
    assert resp_import.status_code == 200
    assert resp_import.json()["success"] is True

    # Test Export Endpoint
    export_target = tmp_path / "rest_exports"
    resp_export = client.post(
        f"/api/workspace/{sess_id}/export-to-path",
        json={"destination_path": str(export_target)}
    )
    assert resp_export.status_code == 200
    assert resp_export.json()["success"] is True
    # Export creates llama_export_<workspace> subfolder inside destination
    export_actual = Path(resp_export.json()["destination"])
    assert export_actual.exists()
    assert (export_actual / "brief.txt").exists()


@pytest.mark.asyncio
async def test_personal_communication_and_browser_dispatch_lifecycle(temp_workspace):
    """Verifies personal loyal communication track, 2-question clarification gate, and browser email dispatch engine."""
    orch = MetaOrchestrator()
    prompt = "hey i want you 3 mails to the email address anshtiwarisocial@gmail.com with exact subject line hello i am jarvis and body will be different of all 3 mails describing what you feel about me"
    
    # 1. Stage 1: Clarification Gate
    analysis = orch.analyze_intent(prompt, session_id="test_comm_sess")
    assert analysis.track_type == "communication_assistant"
    assert len(analysis.clarifications) >= 2
    clarif_ids = [c.id for c in analysis.clarifications]
    assert "email_delivery_channel" in clarif_ids
    assert "permission_authorization" in clarif_ids

    # 2. Stage 3: DAG Compilation
    session = orch.get_or_create_session("test_comm_sess", vision=prompt)
    session.workspace_path = temp_workspace
    session.mcp = MCPServer(temp_workspace)
    dag_plan = orch.compile_dag_and_synthesize_workers(session)
    assert len(dag_plan.nodes) == 4
    node_ids = [n.id for n in dag_plan.nodes]
    assert "task_comm_dispatch_engine" in node_ids

    # 3. Stage 4: Worker Execution
    worker = DynamicWorkerEngine(mcp=session.mcp)
    for node in dag_plan.nodes:
        spec = orch.get_subagent_spec(node.agent_type, session)
        ok = await worker.execute_task(node, spec, track_type="communication_assistant")
        assert ok is True

    # Check deliverables
    assert (temp_workspace / "mail_1.md").exists()
    assert (temp_workspace / "mail_2.md").exists()
    assert (temp_workspace / "mail_3.md").exists()
    assert (temp_workspace / "browser_send_emails.py").exists()
    assert (temp_workspace / "send_emails_smtp.py").exists()
    assert (temp_workspace / "browser_permission_granted.json").exists()
    assert (temp_workspace / "emails.json").exists()
    assert (temp_workspace / "dispatch_summary.md").exists()

    mail_1_content = (temp_workspace / "mail_1.md").read_text(encoding="utf-8")
    assert "hello i am jarvis" in mail_1_content
    assert "anshtiwarisocial@gmail.com" in mail_1_content
    assert "Ansh" in mail_1_content

    # 4. Stage 5: Evaluator Gatekeeper
    evaluator = EvaluatorGatekeeper(mcp=session.mcp)
    report = await evaluator.evaluate_deliverables("test_comm_sess", track_type="communication_assistant")
    assert report["passed"] is True
    assert report["score_percentage"] == 100.0


@pytest.mark.asyncio
async def test_saved_workflows_persistent_pc_scheduler_and_pinning(temp_workspace):
    """Verifies saved workflow CRUD, 24/7 background scheduler logic, natural language scheduling, and chat pinning."""
    from core.orchestrator import HistoryManager, parse_schedule_directive
    hm = HistoryManager()

    # 1. Test Chat Pinning and Sorting
    hm.record_session("sess_unpinned", "Unpinned Task", "Prompt 1")
    hm.record_session("sess_pinned", "Pinned Task", "Prompt 2")
    hm.toggle_pin("sess_pinned", True)

    history = hm.list_history()
    assert len(history) >= 2
    # First item should be the pinned session!
    assert history[0]["session_id"] == "sess_pinned"
    assert history[0]["is_pinned"] is True

    # 2. Test Saved Workflows CRUD
    wf_data = {
        "id": "wf_test_agency",
        "title": "B2B SaaS Lead Generator",
        "prompt": "Find 50 Series A leads and draft cold outreach",
        "folder": "Business"
    }
    hm.save_workflow(wf_data)
    wfs = hm.list_workflows()
    assert any(w["id"] == "wf_test_agency" for w in wfs)

    del_ok = hm.delete_workflow("wf_test_agency")
    assert del_ok is True
    wfs_after = hm.list_workflows()
    assert not any(w["id"] == "wf_test_agency" for w in wfs_after)

    # 3. Test Natural Language Schedule Directive Parsing
    directive = "do this particular work for everyday at 6am: scrape 20 leads and send emails"
    parsed = parse_schedule_directive(directive)
    assert parsed is not None
    assert parsed["hour"] == 6
    assert parsed["minute"] == 0
    assert "scrape 20 leads" in parsed["prompt"]
    assert "Daily 06:00" in parsed["schedule_cron"]

    # Test alternate format "daily at 18:30"
    parsed_pm = parse_schedule_directive("daily at 6pm check crypto portfolio")
    assert parsed_pm is not None
    assert parsed_pm["hour"] == 18

    # 4. Test Scheduled Task Management (CRUD, Toggle, Status)
    sched_entry = hm.add_schedule(parsed)
    assert sched_entry["hour"] == 6
    assert sched_entry["is_active"] is True

    schedules = hm.list_schedules()
    assert any(s["task_id"] == sched_entry["task_id"] for s in schedules)

    # Toggle active status to paused
    toggled = hm.toggle_schedule(sched_entry["task_id"], False)
    assert toggled is True
    updated = next(s for s in hm.list_schedules() if s["task_id"] == sched_entry["task_id"])
    assert updated["is_active"] is False

    # Update run status
    hm.update_schedule_run_status(sched_entry["task_id"], "2026-10-29")
    ran = next(s for s in hm.list_schedules() if s["task_id"] == sched_entry["task_id"])
    assert ran["last_run_date"] == "2026-10-29"
    assert ran["run_count"] == 1

    # Delete schedule
    del_sched = hm.delete_schedule(sched_entry["task_id"])
    assert del_sched is True
    assert not any(s["task_id"] == sched_entry["task_id"] for s in hm.list_schedules())

    # 5. Test REST Endpoints via TestClient
    client = TestClient(app)

    # Test Pin Endpoint
    pin_res = client.post("/api/history/pin", json={"session_id": "sess_pinned", "is_pinned": False})
    assert pin_res.status_code == 200

    # Test Schedules API
    sched_post = client.post("/api/schedules", json={
        "title": "Daily 6AM Test Run",
        "prompt": "Test prompt",
        "hour": 6,
        "minute": 0
    })
    assert sched_post.status_code == 200
    task_id = sched_post.json()["schedule"]["task_id"]

    sched_list = client.get("/api/schedules")
    assert sched_list.status_code == 200
    assert any(s["task_id"] == task_id for s in sched_list.json())

    # Test Run Now
    run_now = client.post(f"/api/schedules/{task_id}/run-now")
    assert run_now.status_code == 200

    # Test Delete Schedule Endpoint
    del_res = client.delete(f"/api/schedules/{task_id}")
    assert del_res.status_code == 200






