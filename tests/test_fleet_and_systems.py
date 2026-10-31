"""
Tests for Jarvis Multi-Account Fleet Engine & Dynamic System Builder
Verifies:
1. 20-Account Fleet Load Balancing & Rate Limit Compliance (25-100 emails/account/day).
2. Continuous Reply Processing & Lead Categorization.
3. Autonomous Software Synthesis, Sandboxed Unit Verification & Registration.
4. Cognitive Self-Awareness of Constructed Systems.
5. Multi-turn CoT Reasoning & Dynamic Strategy Pivots (SMTP / Email provision).
6. Autonomous Link & Destination Target Deduction (Zero Hardcoding).
"""

import pytest
from pathlib import Path
from core.account_fleet import AccountFleetManager, ManagedAccount, ProspectLead
from core.dynamic_system_builder import DynamicSystemBuilder, ConstructedSystem
from core.creator_memory import CreatorMemory
from core.browser_agent import BrowserAgent


def test_fleet_manager_initialization_and_capacity(tmp_path):
    store_file = tmp_path / "test_fleet.json"
    fleet = AccountFleetManager(storage_path=store_file)
    summary = fleet.get_fleet_summary(platform="gmail")

    assert summary["total_accounts"] == 20
    assert summary["ready_accounts"] == 20
    assert summary["total_daily_capacity"] >= 500  # Combined capacity > 500
    assert summary["total_sent_today"] == 0
    assert summary["remaining_capacity"] == summary["total_daily_capacity"]


def test_fleet_rotation_and_load_balancing(tmp_path):
    store_file = tmp_path / "test_fleet_rot.json"
    fleet = AccountFleetManager(storage_path=store_file)

    # First account selected
    acc1 = fleet.select_next_account("gmail")
    assert acc1 is not None
    initial_id = acc1.account_id

    # Simulate sending up to limit
    acc1.sent_today = acc1.daily_limit
    acc1.status = "COOLDOWN"

    # Next rotation must pick a different, ready account
    acc2 = fleet.select_next_account("gmail")
    assert acc2 is not None
    assert acc2.account_id != initial_id
    assert acc2.sent_today < acc2.daily_limit


@pytest.mark.asyncio
async def test_fleet_dispatch_touch_and_reply_monitoring(tmp_path):
    store_file = tmp_path / "test_fleet_dispatch.json"
    fleet = AccountFleetManager(storage_path=store_file)
    fleet.campaigns_path = tmp_path / "test_campaigns.json"

    lead = ProspectLead(email="lead@techcorp.com", name="Alex", company="TechCorp")
    fleet.prospects[lead.email] = lead

    res = await fleet.dispatch_next_touch(lead, "Collaboration", "Hi {{name}} at {{company}}")
    assert res["success"] is True
    assert lead.status == "SENT"
    assert lead.current_touch == 1
    assert res["sent_today_for_account"] == 1

    # Incoming Reply Processing
    reply_res = fleet.process_incoming_reply(
        "lead@techcorp.com",
        "Hi, let's schedule a call on Zoom this week to discuss pricing."
    )
    assert reply_res["status"] == "REPLIED"
    assert reply_res["sentiment_category"] in ["MEETING_REQUEST", "HIGH_INTENT"]
    assert lead.status == "REPLIED"


@pytest.mark.asyncio
async def test_dynamic_system_builder_synthesis_and_execution(tmp_path):
    catalog_file = tmp_path / "test_catalog.json"
    builder = DynamicSystemBuilder(catalog_path=catalog_file)
    builder.systems_dir = tmp_path / "constructed"

    # Autonomous software creation for a custom task
    res = await builder.construct_software_autonomously(
        task_description="Extract and validate email schemas from raw strings",
        system_name="EmailValidatorEngine"
    )
    assert res["success"] is True
    assert res["status"] == "CERTIFIED"
    assert Path(res["entrypoint"]).exists()

    # Cognitive lookup: find matching system
    found = builder.find_matching_system("EmailValidatorEngine")
    assert found is not None
    assert found.system_id == res["system_id"]

    # Execute system
    exec_res = builder.execute_system(found.system_id, ["test@domain.com"])
    assert exec_res["success"] is True
    assert exec_res["duration_sec"] >= 0


def test_creator_memory_multi_turn_cot_and_strategy_pivots(tmp_path):
    mem_file = tmp_path / "test_mem.json"
    memory = CreatorMemory(memory_path=mem_file)

    # Strategy pivot to SMTP
    resp1 = memory.chat_response("can we go smtp way instead of browser?", is_mock=True)
    assert "smtp" in resp1["text"].lower()
    assert resp1.get("strategy") == "smtp_relay"
    assert "thought" in resp1

    # Injecting email address in conversational context
    resp2 = memory.chat_response("ok i will be providing you mail address anshtiwarif17@gmail.com", is_mock=True)
    assert "anshtiwarif17@gmail.com" in resp2["text"].lower()

    # Conversation history tracked
    assert len(memory.conversation_history) >= 4


def test_browser_agent_dynamic_link_deduction():
    # Direct explicit URL
    url1 = BrowserAgent.resolve_target_url_autonomously("visit https://example.com/api")
    assert url1 == "https://example.com/api"

    # Domain syntax deduction
    url2 = BrowserAgent.resolve_target_url_autonomously("check leetcode.com streak")
    assert "leetcode.com" in url2

    # Platform deduction
    url3 = BrowserAgent.resolve_target_url_autonomously("find react jobs on upwork")
    assert "upwork.com" in url3

    # General search query deduction or authoritative URL
    url4 = BrowserAgent.resolve_target_url_autonomously("research quantum computing benchmarks")
    assert url4.startswith("http")


@pytest.mark.asyncio
async def test_recursive_subdag_spawning_and_replanning(tmp_path):
    from core.recursive_subdag import RecursiveSubDAGReplanner
    from core.mcp_server import MCPServer
    from core.models import TaskNode, SubAgentSpec

    mcp = MCPServer(workspace_path=tmp_path)
    parent_task = TaskNode(
        id="task_complex_migration",
        title="Database Schema & Event Streaming Migration",
        description="Migrate complex schema with foreign key constraints",
        agent_type="backend_core_engineer"
    )
    parent_spec = SubAgentSpec(
        agent_id="backend_core_engineer",
        name="Backend Core Engineer",
        role="Executes distributed backend systems",
        system_prompt="Autonomous engineer prompt",
        allowed_tools=["tool_write_file", "tool_run_command"]
    )

    res = await RecursiveSubDAGReplanner.spawn_and_execute_subdag(
        parent_task=parent_task,
        parent_spec=parent_spec,
        failure_context="Deadlock detected during schema migration",
        mcp=mcp
    )

    assert res.success is True
    assert parent_task.status == "completed"
    assert len(parent_task.output_artifacts) > 0
    assert any("recovered_" in f for f in parent_task.output_artifacts)
    assert (tmp_path / parent_task.output_artifacts[0]).exists()


def test_rea_powerup_engine(tmp_path):
    from core.rea_powerup import ReverseEngineerAnythingEngine

    # 1. Inspect Binary test
    dummy_bin = tmp_path / "sample.dll"
    dummy_bin.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00ExportedFunction1\x00https://api.internal.service/v1\x00")
    bin_res = ReverseEngineerAnythingEngine.inspect_binary(str(dummy_bin))
    assert bin_res["success"] is True
    assert "PE" in bin_res["binary_format"]
    assert any("ExportedFunction1" in s for s in bin_res["sample_symbols"])
    assert any("https://api.internal.service/v1" in ep for ep in bin_res["discovered_api_routes"])

    # 2. Unpack Electron test
    dummy_asar = tmp_path / "app.asar"
    dummy_asar.write_bytes(b'ipcRenderer.send("auth:login"); fetch("/api/v2/telemetry");')
    asar_res = ReverseEngineerAnythingEngine.unpack_electron(str(dummy_asar))
    assert asar_res["success"] is True
    assert "auth:login" in asar_res["ipc_channels"]
    assert "/api/v2/telemetry" in asar_res["discovered_endpoints"]

    # 3. Traffic analysis test
    dummy_har = tmp_path / "traffic.har"
    dummy_har.write_text('{"request": {"url": "https://api.target.com/user/profile", "headers": [{"Authorization": "Bearer token123"}]}}', encoding="utf-8")
    har_res = ReverseEngineerAnythingEngine.analyze_traffic(str(dummy_har))
    assert har_res["success"] is True
    assert any("https://api.target.com" in u for u in har_res["extracted_endpoints"])

    # 4. Clean-room client generator test
    client_code = ReverseEngineerAnythingEngine.synthesize_clean_room_client("TargetService", ["/v1/auth", "/v1/metrics"])
    assert "class TargetServiceClient:" in client_code
    assert "def call_auth" in client_code
    assert "def call_metrics" in client_code


def test_tactical_discretion_hierarchy():
    from core.tactical_quiver import TacticalDiscretionEngine, ToolTier

    # 1. Conceptual Q&A -> Tier 1 (Never use heavy tools for questions)
    d1 = TacticalDiscretionEngine.evaluate_directive("Explain how neural attention works in transformers")
    assert d1.tier == ToolTier.TIER_1_COGNITIVE
    assert d1.is_rea_appropriate is False

    # 2. Routine browser operation -> Tier 2 Standard (No heavy tools)
    d2 = TacticalDiscretionEngine.evaluate_directive("browse youtube and play radha naam track 2")
    assert d2.tier == ToolTier.TIER_2_STANDARD
    assert d2.is_rea_appropriate is False

    # 3. Fleet & Multi-account automation -> Tier 3 Synthetic
    d3 = TacticalDiscretionEngine.evaluate_directive("manage 20 gmail accounts with rate limits")
    assert d3.tier == ToolTier.TIER_3_SYNTHETIC
    assert d3.is_rea_appropriate is False

    # 4. Closed Binary / Decompilation -> Tier 4 Heavy Tactical Arrow (Legitimate use)
    d4 = TacticalDiscretionEngine.evaluate_directive("reverse engineer legacy_driver.dll and extract endpoints")
    assert d4.tier == ToolTier.TIER_4_TACTICAL_REA
    assert d4.is_rea_appropriate is True

    # 5. Briefing generation
    briefing = TacticalDiscretionEngine.format_tactical_briefing(d4)
    assert "Tactical Discretion Protocol" in briefing
    assert "Heavy Tactical Arrow" in briefing


def test_mcp_server_rea_tools_integration(tmp_path):
    from core.mcp_server import MCPServer

    mcp = MCPServer(workspace_path=tmp_path)
    defs = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in defs]

    assert "rea_inspect_binary" in tool_names
    assert "rea_unpack_electron" in tool_names
    assert "rea_analyze_traffic" in tool_names
    assert "rea_clone_client" in tool_names
    assert "rea_extract_strings" in tool_names
    assert "rea_scan_secrets" in tool_names
    assert "rea_inspect_ipc" in tool_names
    assert "rea_harvest_routes" in tool_names
    assert "rea_audit_security" in tool_names

    # Test JSON-RPC invocation of rea_clone_client
    rpc_req = {
        "jsonrpc": "2.0",
        "id": 42,
        "method": "tools/call",
        "params": {
            "name": "rea_clone_client",
            "arguments": {
                "service_name": "AutonomousBroker",
                "endpoints": ["/v1/orders", "/v1/positions"]
            }
        }
    }
    rpc_res = mcp.handle_jsonrpc(rpc_req)
    assert rpc_res["result"]["success"] is True
    assert "class AutonomousBrokerClient:" in rpc_res["result"]["client_code"]


def test_granular_rea_surgical_tools(tmp_path):
    from core.rea_powerup import ReverseEngineerAnythingEngine

    # 1. Forensic string extraction
    target_cache = tmp_path / "cache.dat"
    target_cache.write_bytes(b"\x00\x01\x02DATABASE_URL=postgres://admin:secret@db.prod.io:5432/core\x00\x04SESSION_TOKEN_1234567\x00")
    str_res = ReverseEngineerAnythingEngine.extract_strings(str(target_cache), min_length=6, filter_pattern="DATABASE_URL")
    assert str_res["success"] is True
    assert any("postgres://admin" in s for s in str_res["sample_strings"])

    # 2. Secret & credential auditing
    config_file = tmp_path / "config.env"
    config_file.write_text(
        "OPENAI_KEY=sk-abcdefghijklmnopqrstuvwxyz123456789\n"
        "AWS_KEY=AKIAIOSFODNN7EXAMPLE\n"
        "GITHUB_PAT=ghp_1234567890abcdefghijklmnopqrstuv\n",
        encoding="utf-8"
    )
    secret_res = ReverseEngineerAnythingEngine.scan_secrets_and_keys(str(config_file))
    assert secret_res["success"] is True
    assert secret_res["secrets_detected"] >= 3
    found_types = [f["type"] for f in secret_res["findings"]]
    assert "OpenAI API Key" in found_types
    assert "AWS Access Key ID" in found_types
    assert "GitHub Token" in found_types

    # 3. Route & Endpoint Harvester
    traffic_file = tmp_path / "api_traffic.json"
    traffic_file.write_text('{"request": {"url": "https://api.gateway.internal/v2/webhooks"}}', encoding="utf-8")
    harvest_res = ReverseEngineerAnythingEngine.harvest_api_endpoints(str(traffic_file))
    assert harvest_res["success"] is True
    assert harvest_res["endpoints_count"] >= 1
    assert any("webhooks" in ep for ep in harvest_res["endpoints"])

    # 4. Binary Security Auditor
    dummy_pe = tmp_path / "protected.exe"
    dummy_pe.write_bytes(b"MZ\x90\x00VirtualAlloc\x00VirtualProtect\x00CreateRemoteThread\x00system\x00")
    audit_res = ReverseEngineerAnythingEngine.audit_binary_security(str(dummy_pe))
    assert audit_res["success"] is True
    assert audit_res["format"] == "PE"
    assert "VirtualAlloc" in audit_res["suspicious_apis_imported"]
    assert audit_res["risk_tier"] == "ELEVATED"

