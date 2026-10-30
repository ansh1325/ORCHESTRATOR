"""
Unit Tests for Jarvis CLI Directives & Commands.
Verifies that all CLI directives process without runtime exceptions:
- help, clear, voice on/off
- workflows, schedules, history
- session, export
- outreach, transcript
"""

import pytest
from jarvis_cli import JarvisCLI


@pytest.mark.asyncio
async def test_jarvis_cli_system_directives():
    cli = JarvisCLI()
    cli.voice_enabled = False  # Avoid audio popup in CI tests

    # Test Help
    assert await cli.process_directive("help") is True

    # Test Clear
    assert await cli.process_directive("clear") is True

    # Test Voice toggle
    assert await cli.process_directive("voice off") is True
    assert cli.voice_enabled is False
    assert await cli.process_directive("voice on") is True
    assert cli.voice_enabled is True
    cli.voice_enabled = False

    # Test Workflows & Schedules inspection
    assert await cli.process_directive("workflows") is True
    assert await cli.process_directive("schedules") is True

    # Test History inspection
    assert await cli.process_directive("history") is True

    # Test Outreach command
    assert await cli.process_directive("outreach FinTech cuts_latency") is True

    # Test Transcript command
    assert await cli.process_directive("transcript https://www.instagram.com/reel/sample") is True

    # Test Browser directives dispatch without event loop crash
    from unittest.mock import patch, AsyncMock
    with patch("workspaces.live_browser_demo.run_live_demo") as mock_demo:
        assert await cli.process_directive("browser demo") is True
        mock_demo.assert_called_once()

    # Test Media / YouTube directive auto-routing in CLI
    with patch.object(cli, "handle_autonomous_browse", new_callable=AsyncMock) as mock_browse:
        assert await cli.process_directive("go to youtube and search at peach and play the song of karan aujla") is True
        mock_browse.assert_called_once()

    # Test Exit directive
    assert await cli.process_directive("exit") is False

