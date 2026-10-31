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

    # Test Transcript command with mocked solver to avoid external network delay
    from unittest.mock import patch, AsyncMock
    with patch("core.autonomous_solver.CreativeProblemSolver.extract_media_transcript_without_api") as mock_solver:
        mock_solver.return_value = {"success": True, "transcript": "Sample transcript", "deduction_log": ["Step 1"]}
        assert await cli.process_directive("transcript https://www.instagram.com/reel/sample") is True

    # Test Browser directives dispatch without event loop crash
    with patch("workspaces.live_browser_demo.run_live_demo") as mock_demo:
        assert await cli.process_directive("browser demo") is True
        mock_demo.assert_called_once()

    # Test Browser Session close directive
    assert await cli.process_directive("close browser") is True

    # Test Media / YouTube directive auto-routing in CLI
    with patch.object(cli, "handle_autonomous_browse", new_callable=AsyncMock) as mock_browse:
        assert await cli.process_directive("go to youtube and search at peach and play the song of karan aujla") is True
        mock_browse.assert_called_once()

    # Test Conversational / Semantic Session Recall
    assert await cli.process_directive("go to latest session") is True
    assert await cli.process_directive("go to session we talked about making multiple robots") is True

    # Test Self-Codebase Introspection in Chat
    from core.creator_memory import creator_memory
    chat_resp = creator_memory.chat_response("read your own code in core/browser_agent.py and tell me what it does")
    assert "codebase" in chat_resp["text"].lower() or "browser" in chat_resp["text"].lower()

    # Test Exit directive
    assert await cli.process_directive("exit") is False


def test_resolve_external_requirements(tmp_path):
    """Verify autonomous resolution and ingestion of external requirement documents."""
    spec_file = tmp_path / "architecture_spec.md"
    spec_file.write_text("# Telemetry API\nBuild a real-time event pipeline.", encoding="utf-8")

    # Explicit path resolution
    aug, resolved = JarvisCLI.resolve_external_requirements(f"build app using {spec_file}")
    assert resolved == spec_file
    assert "INGESTED SPECIFICATION FROM architecture_spec.md" in aug
    assert "Build a real-time event pipeline." in aug

    # Whole directory / codebase ingestion test
    codebase_dir = tmp_path / "legacy_app"
    codebase_dir.mkdir()
    (codebase_dir / "package.json").write_text('{"name": "legacy-service", "version": "1.0.0"}', encoding="utf-8")
    (codebase_dir / "server.js").write_text('const express = require("express"); app.listen(3000);', encoding="utf-8")

    aug_dir, resolved_dir = JarvisCLI.resolve_external_requirements(f"improve and refactor {codebase_dir}")
    assert resolved_dir == codebase_dir
    assert "INGESTED PRODUCTION CODEBASE:" in aug_dir
    assert "legacy_app" in aug_dir
    assert "package.json" in aug_dir
    assert "server.js" in aug_dir

    # Test finding a specific file inside a directory recursively
    data_dir = tmp_path / "raw_data"
    data_dir.mkdir()
    sub_dir = data_dir / "nested"
    sub_dir.mkdir()
    target_csv = sub_dir / "metrics.csv"
    target_csv.write_text("user,score\nansh,100", encoding="utf-8")

    aug_find, resolved_find = JarvisCLI.resolve_external_requirements(f"find metrics.csv in {data_dir} and clean it")
    assert resolved_find == target_csv
    assert "INGESTED SPECIFICATION FROM metrics.csv" in aug_find
    assert "user,score" in aug_find


def test_universal_login_targets_and_workflow_evolution(tmp_path):
    """Verify universal login portal resolution (LinkedIn, AWS, GitHub) and repetition detection."""
    from core.browser_controller import BrowserController
    from core.creator_memory import CreatorMemory

    # 1. Verify universal login portal resolution
    url_li, name_li = BrowserController.resolve_login_target("linkedin")
    assert "linkedin.com" in url_li
    assert name_li == "LinkedIn"

    url_aws, name_aws = BrowserController.resolve_login_target("aws")
    assert "aws.amazon.com" in url_aws
    assert "aws" in name_aws.lower() or "amazon" in name_aws.lower()

    url_gh, name_gh = BrowserController.resolve_login_target("github")
    assert "github.com" in url_gh

    # 2. Verify repetition detection and workflow promotion
    mem_file = tmp_path / "test_memory.json"
    mem = CreatorMemory(memory_path=mem_file)

    task_directive = "scrape latest AI funding rounds and export to csv"
    rep1 = mem.track_and_detect_repetition(task_directive)
    assert rep1["is_repeated"] is False
    assert rep1["count"] == 1

    rep2 = mem.track_and_detect_repetition(task_directive)
    assert rep2["is_repeated"] is True
    assert rep2["count"] == 2
    assert "wf_auto_" in rep2["workflow_id"]


@pytest.mark.asyncio
async def test_browser_login_command_sanitization(tmp_path):
    """Verify trailing semicolon sanitization and direct auth session routing for browser login;"""
    import json
    from unittest.mock import patch
    from jarvis_cli import JarvisCLI
    from core.browser_controller import BrowserController

    cli = JarvisCLI()
    cli.voice_enabled = False

    # 1. Test clean_profile_crash_state
    pref_dir = tmp_path / "Default"
    pref_dir.mkdir(parents=True)
    pref_file = pref_dir / "Preferences"
    pref_file.write_text(json.dumps({"profile": {"exit_type": "Crashed", "exited_cleanly": False}}), encoding="utf-8")

    BrowserController.clean_profile_crash_state(tmp_path)
    cleaned = json.loads(pref_file.read_text(encoding="utf-8"))
    assert cleaned["profile"]["exit_type"] == "Normal"
    assert cleaned["profile"]["exited_cleanly"] is True

    # 2. Test that 'browser login;' triggers launch_login_session with 'google'
    with patch("core.browser_controller.BrowserController.launch_login_session") as mock_login:
        mock_login.return_value = {"success": True, "logged_in": True, "service": "Google Account"}
        res = await cli.process_directive("browser login;")
        assert res is True
        mock_login.assert_called_once_with("google", None)

    # 3. Test that bare 'login leetcode;' routes directly to launch_login_session
    with patch("core.browser_controller.BrowserController.launch_login_session") as mock_login_lc:
        mock_login_lc.return_value = {"success": True, "logged_in": True, "service": "LeetCode"}
        res = await cli.process_directive("login leetcode;")
        assert res is True
        mock_login_lc.assert_called_once_with("leetcode", None)

    # 4. Test natural language user login request
    with patch("core.browser_controller.BrowserController.launch_login_session") as mock_login_nat:
        mock_login_nat.return_value = {"success": True, "logged_in": True, "service": "Google Account"}
        res = await cli.process_directive("i want to login in browser windows of yours so you can do what i want in my accounts")
        assert res is True
        mock_login_nat.assert_called_once_with("google", None)

