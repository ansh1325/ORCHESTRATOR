"""
Unit & Integration Tests for JARVIS Proactive Ambient System Daemon
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from unittest.mock import MagicMock, patch

from core.jarvis_daemon import JarvisDaemon
from core.mcp_server import MCPServer


def test_hardware_telemetry_collection():
    """Verifies collection of CPU, RAM, and Disk metrics."""
    telem = JarvisDaemon.check_hardware_telemetry()
    assert "cpu_percent" in telem
    assert "memory_percent" in telem
    assert "memory_available_gb" in telem
    assert "disk_free_gb" in telem
    assert telem["status"] in ["HEALTHY", "WARNING_HIGH_LOAD", "CRITICAL_PRESSURE"]


def test_port_safety_inspection():
    """Verifies that development ports are probed for bind availability."""
    ports = JarvisDaemon.inspect_port_safety(ports=[8000, 3000, 5000])
    assert len(ports) == 3
    for p in ports:
        assert "port" in p
        assert "available" in p
        assert p["status"] in ["FREE", "IN_USE"]


def test_daemon_alert_recording_and_cycle(tmp_path):
    """Verifies alert recording to json file and single health cycle run."""
    with patch.object(JarvisDaemon, "ALERTS_FILE", tmp_path / "test_alerts.json"):
        daemon = JarvisDaemon(check_interval_seconds=1.0)
        report = daemon.run_health_cycle()
        assert "telemetry" in report
        assert "ports" in report

        # Record manual test alert
        alt = daemon.record_alert("WARNING", "Test warning alert", {"test": True})
        assert alt["level"] == "WARNING"
        assert len(daemon.alert_history) >= 1

        # Check status
        status = daemon.get_status()
        assert "telemetry" in status
        assert "recent_alerts" in status


def test_mcp_system_health_integration(tmp_path):
    """Verifies MCP server exposes system_health_check."""
    mcp = MCPServer(workspace_path=tmp_path)
    res = mcp.tool_system_health_check()
    assert "cpu_percent" in res
    assert "memory_percent" in res

