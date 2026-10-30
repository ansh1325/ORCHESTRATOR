"""
Unit and Integration Tests for Autonomous Browser Agent & Perception-Action Loop.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.browser_agent import BrowserAgent, BrowserElement, browser_agent
from main import app


def test_browser_element_structure():
    """Verify BrowserElement dataclass integrity."""
    el = BrowserElement(
        index=1,
        tag="button",
        element_type="submit",
        text="Search",
        selector="#search-btn",
        aria_label="Submit Search Query",
        placeholder=""
    )
    assert el.index == 1
    assert el.tag == "button"
    assert el.element_type == "submit"
    assert el.text == "Search"
    assert el.selector == "#search-btn"
    assert el.is_visible is True


def test_browser_agent_initialization(tmp_path):
    """Verify BrowserAgent initializes with persistent profile directory."""
    agent = BrowserAgent(user_data_dir=str(tmp_path / "test_profile"), headless=True)
    assert agent.headless is True
    assert agent.user_data_dir.exists()
    assert agent.screenshot_dir.exists()


def test_browser_agent_decision_heuristic():
    """Verify heuristic action fallback when searching or clicking."""
    agent = BrowserAgent(headless=True)
    elements = [
        BrowserElement(1, "input", "text", "", "input[name='q']", placeholder="Search Google"),
        BrowserElement(2, "button", "submit", "Search", "button#submit")
    ]
    summary = agent._build_dom_summary(MagicMock(url="https://google.com", title=lambda: "Google"), elements)
    assert "PAGE TITLE: Google" in summary
    assert "[#1] INPUT (text): \"Search Google\"" in summary

    # Decision for search query
    decision = agent._decide_next_action("search for python", summary, elements, [])
    assert decision["action"] == "type"
    assert decision["element_id"] == 1
    assert "python" in decision["text"]


def test_browser_agent_email_dispatch_bridge():
    """Verify BrowserAgent email dispatch invokes Playwright and falls back cleanly to host browser compose."""
    agent = BrowserAgent(headless=True)
    with patch("core.browser_controller.BrowserController.automate_gmail_dispatch_playwright") as mock_pw, \
         patch("core.browser_controller.BrowserController.compose_in_gmail") as mock_compose:

        # Case 1: Playwright sends automatically
        mock_pw.return_value = {
            "success": True,
            "sent_automatically": True,
            "screenshot": "screen.png",
            "actions": ["Typed email", "Clicked Send"]
        }
        res1 = agent.send_email_autonomously("test@example.com", "Hello", "Body content")
        assert res1["success"] is True
        assert res1["method"] == "autonomous_playwright_dispatch"

        # Case 2: Playwright requires login -> Seamless Host Browser Bridge
        mock_pw.return_value = {
            "success": True,
            "sent_automatically": False,
            "status": "dispatched_via_host_browser"
        }
        mock_compose.return_value = {"success": True, "action": "open_gmail_compose"}
        res2 = agent.send_email_autonomously("test@example.com", "Hello", "Body content")
        assert res2["success"] is True
        assert res2["method"] == "host_browser_authenticated_session"
        assert mock_compose.called


def test_browser_agent_fastapi_endpoints():
    """Verify REST API endpoints for Browser Agent."""
    client = TestClient(app)

    with patch.object(browser_agent, "execute_goal") as mock_exec, \
         patch.object(browser_agent, "send_email_autonomously") as mock_email:

        mock_exec.return_value = {
            "success": True,
            "final_url": "https://example.com",
            "final_title": "Example Domain",
            "summary": "Completed search",
            "execution_log": ["Navigated to example.com"]
        }
        mock_email.return_value = {
            "success": True,
            "recipient": "anshtiwarif17@gmail.com",
            "message": "Opened in host browser ready for 1-click dispatch."
        }

        # 1. Execute goal endpoint
        res = client.post("/api/browser/agent/execute", json={"goal": "check weather in New York", "max_steps": 3})
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["final_title"] == "Example Domain"

        # 2. Email dispatch endpoint
        email_res = client.post("/api/browser/agent/email", json={
            "recipient": "anshtiwarif17@gmail.com",
            "subject": "hello i am jarvis",
            "body": "Test message from autonomous agent"
        })
        assert email_res.status_code == 200
        assert email_res.json()["success"] is True
