"""
Unit & Integration Tests for JARVIS Universal Desktop GUI Operator
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.os_operator import OSOperator
from core.mcp_server import MCPServer


def test_get_screen_resolution():
    """Verifies that primary screen resolution is detected."""
    w, h = OSOperator.get_screen_resolution()
    assert isinstance(w, int) and w > 0
    assert isinstance(h, int) and h > 0


def test_get_cursor_position():
    """Verifies mouse cursor position retrieval."""
    x, y = OSOperator.get_cursor_position()
    assert isinstance(x, int)
    assert isinstance(y, int)


def test_capture_desktop_screen(tmp_path):
    """Verifies screenshot capture produces valid PNG artifact."""
    dest = tmp_path / "test_screenshot.png"
    with patch.object(OSOperator, "SCREENSHOT_DIR", tmp_path):
        res_path = OSOperator.capture_desktop_screen("test_screenshot.png")
        assert res_path.exists()
        assert res_path.stat().st_size > 0


def test_list_running_applications():
    """Verifies enumeration of running GUI and system processes."""
    apps = OSOperator.list_running_applications()
    assert isinstance(apps, list)
    # At least python and powershell/system processes should be detected
    assert len(apps) >= 1
    sample = apps[0]
    assert "name" in sample
    assert "pid" in sample
    assert "memory_mb" in sample


def test_execute_desktop_directive():
    """Verifies unified cognitive action gateway for desktop commands."""
    res_apps = OSOperator.execute_desktop_directive("apps")
    assert res_apps["success"] is True
    assert "telemetry" in res_apps

    res_cap = OSOperator.execute_desktop_directive("screen", filename="test_cognitive.png")
    assert res_cap["success"] is True

    res_click = OSOperator.execute_desktop_directive("click", x=100, y=100, button="left")
    assert res_click["success"] is True

    res_hotkey = OSOperator.execute_desktop_directive("hotkey", keys=["ctrl", "s"])
    assert res_hotkey["success"] is True


def test_mcp_desktop_tools_integration(tmp_path):
    """Verifies that MCPServer exposes and executes desktop tools seamlessly."""
    mcp = MCPServer(workspace_path=tmp_path)
    tools = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in tools]
    assert "desktop_execute" in tool_names
    assert "desktop_screenshot" in tool_names
    assert "desktop_click" in tool_names
    assert "desktop_type" in tool_names
    assert "desktop_hotkey" in tool_names
    assert "desktop_focus_app" in tool_names
    assert "desktop_list_apps" in tool_names

    # Test MCP tool call
    res = mcp.tool_desktop_list_apps()
    assert res["success"] is True
    assert "apps" in res

