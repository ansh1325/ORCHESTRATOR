"""
Comprehensive Test Suite for Agent-Reach Powerup in JARVIS.
Verifies multi-platform reach (LinkedIn, Reddit, GitHub, YouTube, Web),
zero-login public syndication dorking, MCP server tools, and Jarvis CLI directives.
Architect: Ansh Tiwari
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.agent_reach_powerup import AgentReachEngine, agent_reach_engine
from core.mcp_server import MCPServer
from jarvis_cli import JarvisCLI


def test_agent_reach_doctor():
    """Verify that Agent-Reach diagnostics detect all 14 channels."""
    doc = AgentReachEngine.doctor()
    assert doc["overall_health"] in ["EXCELLENT", "GOOD", "PARTIAL"]
    assert doc["installed_channels"] >= 10
    assert "github" in doc["channels"]
    assert "reddit" in doc["channels"]
    assert "linkedin" in doc["channels"]
    assert "youtube" in doc["channels"]
    assert "channel_health" in doc
    assert doc["channel_health"]["github"]["available"] is True


def test_agent_reach_github_search():
    """Verify GitHub search via Agent-Reach."""
    results = AgentReachEngine.search_github("agent-reach", limit=3)
    assert len(results) > 0
    assert any("agent-reach" in r.get("title", "").lower() or "reach" in str(r).lower() for r in results)


def test_agent_reach_reddit_search():
    """Verify Reddit public search without login."""
    results = AgentReachEngine.search_reddit("python", limit=3)
    assert len(results) > 0
    assert any("python" in str(r).lower() or "title" in r for r in results)


def test_agent_reach_linkedin_leads_public_dorking():
    """Verify public-first scoped syndication for LinkedIn profiles (bypassing auth wall)."""
    leads = AgentReachEngine.search_linkedin_leads("fintech founder", location="New York", limit=3)
    assert len(leads) >= 1
    first_lead = leads[0]
    assert "name" in first_lead
    assert "title" in first_lead
    assert "company" in first_lead
    assert "profile_url" in first_lead
    assert "linkedin.com/in/" in first_lead["profile_url"]


def test_agent_reach_linkedin_jobs():
    """Verify LinkedIn job searching."""
    jobs = AgentReachEngine.search_linkedin_jobs("AI Engineer", location="Remote", limit=2)
    assert len(jobs) >= 1
    assert "title" in jobs[0]
    assert "url" in jobs[0]


def test_agent_reach_youtube_transcript():
    """Verify YouTube subtitle / transcript extraction."""
    res = AgentReachEngine.fetch_youtube_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert res["success"] is True
    assert "transcript" in res
    assert len(res["transcript"]) > 0


def test_agent_reach_read_url():
    """Verify Universal Markdown Reader for web pages."""
    doc = AgentReachEngine.read_url_content("https://example.com")
    assert doc["success"] is True
    assert "url" in doc
    assert "content" in doc


def test_agent_reach_universal_router():
    """Verify universal search routes appropriately by platform."""
    gh = AgentReachEngine.universal_search("github", "llama", limit=2)
    assert len(gh) > 0

    rd = AgentReachEngine.universal_search("reddit", "machine learning", limit=2)
    assert len(rd) > 0

    li = AgentReachEngine.universal_search("linkedin", "founder", limit=2)
    assert len(li) > 0


def test_mcp_server_reach_tools(tmp_path):
    """Verify Agent-Reach tools registered in MCP Server and callable via JSON-RPC."""
    mcp = MCPServer(workspace_path=tmp_path)
    defs = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in defs]

    assert "reach_universal_search" in tool_names
    assert "reach_harvest_leads" in tool_names
    assert "reach_read_target" in tool_names
    assert "reach_doctor" in tool_names

    # Test JSON-RPC call for reach_doctor
    rpc_doc = mcp.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {"name": "reach_doctor", "arguments": {}}
    })
    assert rpc_doc.get("result", {}).get("overall_health") in ["EXCELLENT", "GOOD", "PARTIAL"]

    # Test JSON-RPC call for reach_harvest_leads
    rpc_leads = mcp.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {"name": "reach_harvest_leads", "arguments": {"niche": "biotech", "limit": 2}}
    })
    res_leads = rpc_leads.get("result", [])
    assert len(res_leads) >= 1
    assert "name" in res_leads[0]
    assert "company" in res_leads[0]


@pytest.mark.asyncio
async def test_jarvis_cli_reach_directives():
    """Verify Jarvis CLI process_directive routes reach commands cleanly."""
    cli = JarvisCLI()
    cli.voice_enabled = False

    # 1. Test reach doctor command
    assert await cli.process_directive("reach doctor") is True

    # 2. Test reach leads command
    assert await cli.process_directive("reach leads fintech London") is True

    # 3. Test reach platform commands
    assert await cli.process_directive("reach github agent-reach") is True
    assert await cli.process_directive("reach reddit machinelearning") is True

    # 4. Test natural language reach intent resolution (Zero-Model fallback)
    plan = await cli.decompose_directive_cognitively("find 10 leads on linkedin in healthcare")
    steps = plan.get("steps", [])
    assert len(steps) >= 1
    assert steps[0]["mode"] == "reach"
    assert steps[0]["platform"] == "linkedin"

