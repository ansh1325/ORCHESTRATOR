"""
Comprehensive Test Suite for LlamaOrchestrator
Tests all 6 lifecycle stages, MCP sandboxing security, DAG compilation,
and FastAPI REST & SSE endpoints.
"""

import pytest
import shutil
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from core.config import settings
from core.creator_memory import CreatorMemory
from core.mcp_server import MCPServer, MCPSandboxSecurityError
from core.orchestrator import MetaOrchestrator
from core.knowledge_agent import KnowledgeAgent
from core.worker import DynamicWorkerEngine, clean_code_content
from core.evaluator import EvaluatorGatekeeper
from core.models import TaskNode, SubAgentSpec
from main import app

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

    # Actionable building directive
    action_analysis = orch.analyze_intent("launch an omnichannel marketing and client acquisition agency")
    assert action_analysis.response_mode == "swarm_army"
    assert action_analysis.combat_tier in ["tactical_squad", "swarm_army"]




