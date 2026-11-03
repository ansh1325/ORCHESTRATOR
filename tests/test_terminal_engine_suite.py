"""
Test Suite: JARVIS Terminal & Git Execution Engine
==================================================
Verifies full autonomous terminal execution, PortSafetyGuard,
Git lifecycle management, semantic commit synthesis, visible terminal window spawning,
MCP server tool registration (58 tools), and JARVIS Central Brain cognitive routing.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.terminal_engine import TerminalEngine
from core.mcp_server import MCPServer
from jarvis_cli import JarvisCLI


class TestTerminalEngine:
    def test_terminal_doctor(self):
        """Verifies doctor diagnostics for host terminal environment."""
        doc = TerminalEngine.doctor()
        assert "git_installed" in doc
        assert "git_version" in doc
        assert "default_shell" in doc
        assert "python_executable" in doc
        assert "status" in doc
        assert doc["status"] == "ONLINE"
        assert Path(doc["workspace_path"]).exists()

    def test_terminal_run_command_success(self):
        """Verifies basic command execution with stdout and duration metrics."""
        res = TerminalEngine.run_command("python -c \"print('JARVIS_TERMINAL_ONLINE')\"")
        assert res["success"] is True
        assert res["returncode"] == 0
        assert "JARVIS_TERMINAL_ONLINE" in res["stdout"]
        assert res["duration_sec"] >= 0.0

    def test_terminal_dangerous_command_blocked(self):
        """Verifies PortSafetyGuard regex intercepts dangerous system destruction commands."""
        res = TerminalEngine.run_command("format C: /fs:NTFS")
        assert res["success"] is False
        assert res["returncode"] == -1
        assert "Security Alert" in res["stderr"]

    def test_git_status_and_diff(self):
        """Verifies git status returns structured repository inspection."""
        stat = TerminalEngine.git_status()
        assert stat["is_git_repo"] is True
        assert "branch" in stat
        assert "clean" in stat
        assert isinstance(stat["modified"], list)
        assert isinstance(stat["untracked"], list)

        diff = TerminalEngine.git_diff()
        assert isinstance(diff, str)

    def test_git_log(self):
        """Verifies git commit history parsing."""
        commits = TerminalEngine.git_log(limit=3)
        assert isinstance(commits, list)
        if commits:
            assert "hash" in commits[0]
            assert "author" in commits[0]
            assert "message" in commits[0]

    def test_synthesize_semantic_commit_message(self):
        """Verifies autonomous commit message formulation based on git status/diff."""
        msg = TerminalEngine.synthesize_semantic_commit_message()
        assert isinstance(msg, str)
        assert len(msg) > 5
        assert len(msg) < 120

    def test_open_visible_terminal(self):
        """Verifies visible terminal spawner selects valid desktop terminal emulator."""
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 9999
            mock_popen.return_value = mock_proc

            res = TerminalEngine.open_visible_terminal(command="echo Ready")
            assert res["success"] is True
            assert "terminal" in res
            mock_popen.assert_called_once()

    def test_git_commit_and_push_workflow(self, tmp_path):
        """Verifies full autonomous commit and push staging lifecycle."""
        with patch.object(TerminalEngine, "git_status") as mock_status, \
             patch.object(TerminalEngine, "run_command") as mock_run:

            mock_status.return_value = {
                "is_git_repo": True,
                "branch": "main",
                "clean": False,
                "total_changed": 3,
                "staged": [],
                "modified": ["core/terminal_engine.py"],
                "untracked": []
            }

            mock_run.side_effect = [
                {"success": True, "returncode": 0, "stdout": "", "stderr": ""},       # git add -A
                {"success": True, "returncode": 0, "stdout": "[main abc1234] feat", "stderr": ""}, # git commit
                {"success": True, "returncode": 0, "stdout": "abc1234\n", "stderr": ""}, # rev-parse
                {"success": True, "returncode": 0, "stdout": "Everything up-to-date", "stderr": ""} # git push
            ]

            res = TerminalEngine.git_commit_and_push(
                commit_message="feat(terminal): autonomous engine",
                push=True,
                cwd=str(tmp_path)
            )

            assert res["success"] is True
            assert res["committed"] is True
            assert res["pushed"] is True
            assert res["commit_hash"] == "abc1234"
            assert res["commit_message"] == "feat(terminal): autonomous engine"


class TestMCPTerminalTools:
    def test_mcp_terminal_tool_definitions(self, tmp_path):
        """Verifies all 7 Terminal & Git tools are registered in MCP server (at least 62 tools)."""
        server = MCPServer(workspace_path=tmp_path)
        defs = server.get_tool_definitions()
        names = {t["name"] for t in defs}

        assert len(defs) >= 62
        assert "terminal_execute" in names
        assert "git_commit_and_push" in names
        assert "git_status" in names
        assert "git_diff" in names
        assert "git_log" in names
        assert "terminal_open_window" in names
        assert "terminal_doctor" in names

    def test_mcp_terminal_execute_jsonrpc(self, tmp_path):
        """Verifies JSON-RPC dispatch for terminal_execute."""
        server = MCPServer(workspace_path=tmp_path)
        req = {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/call",
            "params": {
                "name": "terminal_execute",
                "arguments": {"command": "python -c \"print('MCP_TERMINAL_OK')\""}
            }
        }
        resp = server.handle_jsonrpc(req)
        assert resp["id"] == 101
        assert "result" in resp
        assert resp["result"]["success"] is True
        assert "MCP_TERMINAL_OK" in resp["result"]["stdout"]

    def test_mcp_git_status_and_doctor_jsonrpc(self, tmp_path):
        """Verifies JSON-RPC dispatch for git_status and terminal_doctor."""
        server = MCPServer(workspace_path=tmp_path)

        req_doc = {
            "jsonrpc": "2.0",
            "id": 102,
            "method": "tools/call",
            "params": {"name": "terminal_doctor", "arguments": {}}
        }
        res_doc = server.handle_jsonrpc(req_doc)
        assert res_doc["result"]["status"] == "ONLINE"

        req_stat = {
            "jsonrpc": "2.0",
            "id": 103,
            "method": "tools/call",
            "params": {"name": "git_status", "arguments": {}}
        }
        res_stat = server.handle_jsonrpc(req_stat)
        assert "is_git_repo" in res_stat["result"]


@pytest.mark.asyncio
class TestJarvisCLITerminalAndGitDirectives:
    async def test_cognitive_decomposition_commit_to_github(self):
        """Verifies Central Brain decomposes 'commit it to github' into terminal mode."""
        cli = JarvisCLI()
        plan = await cli.decompose_directive_cognitively("commit it to github")
        steps = plan.get("steps", [])
        assert len(steps) >= 1
        assert steps[0]["mode"] == "terminal"
        assert steps[0].get("git_action") == "commit_and_push"

    async def test_cognitive_decomposition_run_terminal_command(self):
        """Verifies Central Brain decomposes 'run dir in terminal' into terminal execution."""
        cli = JarvisCLI()
        plan = await cli.decompose_directive_cognitively("run dir in terminal")
        steps = plan.get("steps", [])
        assert len(steps) >= 1
        assert steps[0]["mode"] == "terminal"
        assert "dir" in steps[0].get("command", "")

    async def test_cognitive_decomposition_open_terminal(self):
        """Verifies Central Brain decomposes 'open terminal' into terminal spawner."""
        cli = JarvisCLI()
        plan = await cli.decompose_directive_cognitively("open terminal")
        steps = plan.get("steps", [])
        assert len(steps) >= 1
        assert steps[0]["mode"] == "terminal"
        assert steps[0].get("command") == "open"

    async def test_process_directive_git_status(self):
        """Verifies direct CLI process_directive routing for 'git status'."""
        cli = JarvisCLI()
        with patch.object(cli, "handle_git_cmd") as mock_git:
            ok = await cli.process_directive("git status")
            assert ok is True
            mock_git.assert_called_once()
            assert mock_git.call_args[0][0] == ["git", "status"]

    async def test_process_directive_terminal_open(self):
        """Verifies direct CLI process_directive routing for 'terminal open'."""
        cli = JarvisCLI()
        with patch.object(cli, "handle_terminal_cmd") as mock_term:
            ok = await cli.process_directive("terminal open")
            assert ok is True
            mock_term.assert_called_once()
            assert mock_term.call_args[0][0] == ["terminal", "open"]

    async def test_execute_autonomous_step_terminal_commit(self):
        """Verifies autonomous step execution for Git commit and push."""
        cli = JarvisCLI()
        step = {
            "mode": "terminal",
            "git_action": "commit_and_push",
            "commit_message": "test commit",
            "goal": "commit changes to github"
        }
        with patch("core.terminal_engine.TerminalEngine.git_commit_and_push") as mock_commit:
            mock_commit.return_value = {
                "success": True,
                "committed": True,
                "pushed": True,
                "branch": "main",
                "commit_hash": "f123456",
                "commit_message": "test commit",
                "files_committed": 2
            }
            ok = await cli.execute_autonomous_step(step, original_line="commit it to github")
            assert ok is True
            mock_commit.assert_called_once_with(commit_message="test commit", push=True)

