"""
Unit & Integration Test Suite for JARVIS Crawl4AI Superpower Engine.
=====================================================================
Validates:
1. Crawl4AI engine doctor and diagnostic reporting.
2. Stealth crawling with anti-bot evasion and fit-markdown synthesis.
3. Authenticated scraping via persistent browser session (~/.llama_orchestrator/browser_profile).
4. Concurrent asynchronous batch crawling.
5. Synchronous thread-safe bridges (crawl_url_sync, crawl_auth_walled_sync).
6. Agent-Reach reader synergy with Crawl4AI.
7. MCP Server tool definitions and JSON-RPC execution.
8. Jarvis CLI crawl directives and Central Brain autonomous cognitive decomposition.
"""

import pytest
import asyncio
from pathlib import Path
from core.crawl4ai_powerup import Crawl4AIEngine
from core.agent_reach_powerup import AgentReachEngine
from core.mcp_server import MCPServer
from jarvis_cli import JarvisCLI


def test_crawl4ai_doctor():
    """Verify Crawl4AI doctor returns online status and active capabilities."""
    health = Crawl4AIEngine.doctor()
    assert health["crawl4ai_installed"] is True
    assert health["engine_status"] == "ONLINE"
    assert "Stealth & Anti-Bot Magic Mode (Patchright)" in health["capabilities"]
    assert "Auth-Walled Platform Scraping (Persistent Browser Profile)" in health["capabilities"]
    assert Path(health["browser_profile_path"]).exists()


@pytest.mark.asyncio
async def test_stealth_crawl_url():
    """Verify Crawl4AI asynchronous stealth crawl with fit-markdown generation."""
    res = await Crawl4AIEngine.crawl_url("https://example.com", magic=True, stealth=True)
    assert res["success"] is True
    assert res["status_code"] == 200
    assert len(res["markdown"]) > 0
    assert len(res["fit_markdown"]) > 0
    assert isinstance(res["links_count"], int)
    assert isinstance(res["internal_links"], list)


@pytest.mark.asyncio
async def test_auth_walled_crawl():
    """Verify Crawl4AI authenticated crawl with persistent browser profile context."""
    res = await Crawl4AIEngine.crawl_auth_walled("https://example.com", service_hint="test_portal")
    assert res["success"] is True
    assert res["status_code"] == 200
    assert res.get("authenticated_session_used") is True
    assert len(res["fit_markdown"]) > 0


@pytest.mark.asyncio
async def test_crawl_batch():
    """Verify asynchronous batch crawling with semaphore control."""
    urls = ["https://example.com", "https://example.org"]
    batch_res = await Crawl4AIEngine.crawl_batch(urls, max_concurrent=2)
    assert len(batch_res) == 2
    for r in batch_res:
        assert r["success"] is True
        assert len(r["markdown"]) > 0


def test_sync_crawl_bridges():
    """Verify synchronous bridges execute without event loop collision."""
    res = Crawl4AIEngine.crawl_url_sync("https://example.com")
    assert res["success"] is True
    assert len(res["markdown"]) > 0

    auth_res = Crawl4AIEngine.crawl_auth_walled_sync("https://example.com")
    assert auth_res["success"] is True
    assert auth_res.get("authenticated_session_used") is True


def test_agent_reach_synergy_with_crawl4ai():
    """Verify Agent-Reach read_url_content seamlessly utilizes Crawl4AI as primary engine."""
    doc = AgentReachEngine.read_url_content("https://example.com")
    assert doc["success"] is True
    assert doc.get("engine") == "crawl4ai"
    assert len(doc["content"]) > 0


def test_mcp_crawl4ai_tools(tmp_path):
    """Verify Crawl4AI tools registered in MCP server and callable via JSON-RPC."""
    mcp = MCPServer(workspace_path=tmp_path)
    tools = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in tools]

    assert "crawl_url" in tool_names
    assert "crawl_auth_walled" in tool_names
    assert "crawl_batch" in tool_names
    assert "crawl_doctor" in tool_names

    # 1. Test crawl_doctor JSON-RPC
    rpc_doc = mcp.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 201,
        "method": "tools/call",
        "params": {"name": "crawl_doctor", "arguments": {}}
    })
    assert rpc_doc.get("result", {}).get("engine_status") == "ONLINE"

    # 2. Test crawl_url JSON-RPC
    rpc_crawl = mcp.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 202,
        "method": "tools/call",
        "params": {"name": "crawl_url", "arguments": {"url": "https://example.com"}}
    })
    res_crawl = rpc_crawl.get("result", {})
    assert res_crawl.get("success") is True
    assert len(res_crawl.get("markdown", "")) > 0


@pytest.mark.asyncio
async def test_jarvis_cli_crawl_directives():
    """Verify Jarvis CLI crawl directives and Central Brain autonomous cognitive planning."""
    cli = JarvisCLI()
    cli.voice_enabled = False

    # 1. Direct CLI crawl doctor
    assert await cli.process_directive("crawl doctor") is True

    # 2. Direct CLI crawl single target
    assert await cli.process_directive("crawl https://example.com") is True

    # 3. Direct CLI crawl auth target
    assert await cli.process_directive("crawl auth https://example.com") is True

    # 4. Central Brain Autonomous Decomposition for public deep crawl
    plan = await cli.decompose_directive_cognitively("crawl https://example.com and extract fit-markdown")
    steps = plan.get("steps", [])
    assert len(steps) >= 1
    assert steps[0]["mode"] == "crawl"
    assert "https://example.com" in (steps[0].get("target_url") or steps[0].get("goal", ""))

    # 5. Central Brain Autonomous Decomposition for auth-walled scraping
    auth_plan = await cli.decompose_directive_cognitively("scrape protected dashboard at https://app.example.com/analytics using my session")
    auth_steps = auth_plan.get("steps", [])
    assert len(auth_steps) >= 1
    assert auth_steps[0]["mode"] == "crawl"
    assert auth_steps[0].get("auth_required") is True

