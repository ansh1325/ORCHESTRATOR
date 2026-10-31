"""
Unit verification for BrowserUseEngine and Deliverable Lead Resolvers.
Architect: Ansh Tiwari
"""

import pytest
from pathlib import Path
from core.browser_use_engine import browser_use_engine
from core.creator_memory import creator_memory
from core.mcp_server import MCPServer
from core.config import settings


def test_browser_use_engine_availability():
    """Verify browser-use package is imported and initialized."""
    assert browser_use_engine.is_available() is True


def test_mcp_server_has_browser_use_tool():
    """Verify tool_browser_use_execute is registered in MCP tool definitions."""
    mcp = MCPServer(workspace_path=settings.WORKSPACE_DIR)
    tool_defs = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in tool_defs]
    assert "browser_use_execute" in tool_names


def test_creator_memory_finds_real_leads():
    """Verify creator memory finds real workspace leads instead of mock Detroit strings."""
    # Ensure at least one test lead file exists in a workspace
    test_session = settings.WORKSPACE_DIR / "test_verification_session"
    test_session.mkdir(parents=True, exist_ok=True)
    test_csv = test_session / "leads.csv"
    test_csv.write_text(
        "Name,Email,Company,Role,Status\n"
        "Alex Thorne,alex@thorne-tech.io,Thorne Tech,CEO,Verified\n"
        "Mira Vance,mira@quantumscale.ai,QuantumScale,CTO,Verified\n",
        encoding="utf-8"
    )

    found = creator_memory.find_latest_workspace_leads()
    assert found is not None
    csv_path, rows = found
    assert len(rows) >= 2
    assert any("thorne" in r.get("Email", "").lower() or "synthetica" in r.get("Email", "").lower() for r in rows)

    # Test markdown table formatter
    table = creator_memory.format_leads_as_markdown(rows)
    assert "| Name | Email | Company |" in table or "| Name |" in table


def test_creator_memory_chat_response_leads_no_refusal():
    """Verify that asking for email list or leads delivers workspace data without LLM refusal."""
    resp = creator_memory.chat_response("give me the email list", is_mock=True)
    assert resp["role"] == "assistant"
    # Must NOT have any canned refusal
    refusal_words = ["cannot give", "can not give", "cannot provide", "as an ai", "sorry, but"]
    assert not any(w in resp["text"].lower() for w in refusal_words)
    # Must contain table or deliverable mention
    assert "verified" in resp["text"].lower() or "leads" in resp["text"].lower() or "source file" in resp["text"].lower()
