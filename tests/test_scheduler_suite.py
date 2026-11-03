"""
Test Suite: JARVIS 24/7 Autonomous Scheduler Engine
====================================================
Verifies natural language schedule parsing, Central Brain cognitive decomposition,
Windows Task Scheduler OS persistence, MCP server tool registration,
and background daemon execution loops.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from core.scheduler import AutonomousScheduler, parse_schedule_directive, scheduler
from core.mcp_server import MCPServer
from jarvis_cli import JarvisCLI


class TestScheduleParsing:
    def test_parse_user_exact_query(self):
        """Verifies parsing of 'every day 6 am go to leetcode and solve a problem'."""
        query = "every day 6 am go to leetcode and solve a problem"
        res = parse_schedule_directive(query)
        assert res is not None
        assert res["hour"] == 6
        assert res["minute"] == 0
        assert res["schedule_cron"] == "Daily 06:00"
        assert "leetcode" in res["prompt"].lower()
        assert "solve" in res["prompt"].lower()
        assert not res["prompt"].lower().startswith("every day 6 am")

    def test_parse_daily_variations(self):
        """Verifies flexible daily phrasing variations."""
        cases = [
            ("daily at 06:00 check crypto portfolio", 6, 0, "check crypto portfolio"),
            ("everyday at 6am commit to github", 6, 0, "commit to github"),
            ("at 6 am every day scrape news", 6, 0, "scrape news"),
            ("every morning 7:30 am check emails", 7, 30, "check emails"),
            ("daily 6pm backup files", 18, 0, "backup files"),
            ("every night 10 pm run tests", 22, 0, "run tests"),
            ("schedule this for daily at 8am send reports", 8, 0, "send reports"),
        ]
        for text, exp_hr, exp_min, exp_keyword in cases:
            res = parse_schedule_directive(text)
            assert res is not None, f"Failed to parse '{text}'"
            assert res["hour"] == exp_hr, f"Hour mismatch for '{text}': got {res['hour']} expected {exp_hr}"
            assert res["minute"] == exp_min, f"Minute mismatch for '{text}'"
            assert exp_keyword in res["prompt"].lower()

    def test_parse_continuous_and_hourly(self):
        """Verifies continuous 24/7 loops and hourly cadences."""
        cont = parse_schedule_directive("run continuously 24/7 monitor leads")
        assert cont is not None
        assert cont["hour"] == -1
        assert cont["minute"] == -1
        assert "24/7" in cont["schedule_cron"] or "Continuous" in cont["schedule_cron"]

        hourly = parse_schedule_directive("every hour sync git repository")
        assert hourly is not None
        assert hourly["hour"] == -1
        assert hourly["minute"] == 0
        assert "Hourly" in hourly["schedule_cron"]

    def test_non_schedule_query(self):
        """Verifies that non-schedule queries return None."""
        assert parse_schedule_directive("solve leetcode problem today") is None
        assert parse_schedule_directive("commit changes to github") is None


class TestSchedulerEngine:
    def test_add_and_list_schedules(self, tmp_path):
        """Verifies schedule persistence and listing."""
        sched = AutonomousScheduler(workspace_dir=tmp_path)
        entry = sched.add_schedule({
            "hour": 6,
            "minute": 0,
            "prompt": "go to leetcode and solve a problem",
            "title": "Daily LeetCode"
        })
        assert entry["task_id"] is not None
        assert entry["hour"] == 6
        assert entry["prompt"] == "go to leetcode and solve a problem"

        items = sched.list_schedules()
        assert len(items) == 1
        assert items[0]["task_id"] == entry["task_id"]

    def test_toggle_and_delete_schedules(self, tmp_path):
        """Verifies schedule activation toggling and deletion."""
        sched = AutonomousScheduler(workspace_dir=tmp_path)
        entry = sched.add_schedule({"hour": 7, "prompt": "check emails"})
        tid = entry["task_id"]

        assert sched.toggle_schedule(tid, False) is True
        item = sched.list_schedules()[0]
        assert item["is_active"] is False

        assert sched.delete_schedule(tid) is True
        assert len(sched.list_schedules()) == 0

    def test_windows_task_registration_mocked(self):
        """Verifies Windows Task Scheduler creation command."""
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "SUCCESS"
            mock_run.return_value = mock_res

            res = AutonomousScheduler.register_windows_task(
                task_id="abc12345",
                hour=6,
                minute=0,
                prompt="go to leetcode and solve a problem"
            )
            if sys.platform == "win32":
                assert res["success"] is True
                assert res["task_name"] == "JARVIS_abc12345"
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                assert "schtasks /Create" in cmd
                assert "/ST 06:00" in cmd


class TestMCPSchedulerTools:
    def test_mcp_scheduler_tool_definitions(self, tmp_path):
        """Verifies all 4 scheduler tools are registered in MCP server (at least 62 tools)."""
        server = MCPServer(workspace_path=tmp_path)
        defs = server.get_tool_definitions()
        names = {t["name"] for t in defs}

        assert len(defs) >= 62
        assert "schedule_add" in names
        assert "schedule_list" in names
        assert "schedule_delete" in names
        assert "schedule_toggle" in names

    def test_mcp_schedule_jsonrpc_workflow(self, tmp_path):
        """Verifies JSON-RPC dispatch for schedule_add, schedule_list, and schedule_delete."""
        server = MCPServer(workspace_path=tmp_path)

        req_add = {
            "jsonrpc": "2.0",
            "id": 201,
            "method": "tools/call",
            "params": {
                "name": "schedule_add",
                "arguments": {
                    "prompt": "every day 6 am go to leetcode and solve a problem",
                    "hour": 6,
                    "minute": 0
                }
            }
        }
        res_add = server.handle_jsonrpc(req_add)
        assert res_add["id"] == 201
        assert "task_id" in res_add["result"]
        tid = res_add["result"]["task_id"]

        req_list = {
            "jsonrpc": "2.0",
            "id": 202,
            "method": "tools/call",
            "params": {"name": "schedule_list", "arguments": {}}
        }
        res_list = server.handle_jsonrpc(req_list)
        assert len(res_list["result"]) >= 1

        req_del = {
            "jsonrpc": "2.0",
            "id": 203,
            "method": "tools/call",
            "params": {"name": "schedule_delete", "arguments": {"task_id": tid}}
        }
        res_del = server.handle_jsonrpc(req_del)
        assert res_del["result"]["success"] is True


@pytest.mark.asyncio
class TestJarvisCLIScheduleDirectives:
    async def test_cognitive_decomposition_user_exact_query(self):
        """Verifies Central Brain decomposes 'every day 6 am go to leetcode and solve a problem' into schedule mode."""
        cli = JarvisCLI()
        plan = await cli.decompose_directive_cognitively("every day 6 am go to leetcode and solve a problem")
        steps = plan.get("steps", [])
        assert len(steps) >= 1
        assert steps[0]["mode"] == "schedule"
        assert steps[0].get("hour") == 6
        assert steps[0].get("minute") == 0

    async def test_execute_autonomous_step_schedule(self):
        """Verifies execution of schedule step registers schedule."""
        cli = JarvisCLI()
        step = {
            "mode": "schedule",
            "hour": 6,
            "minute": 0,
            "schedule_cron": "Daily 06:00",
            "recurring_prompt": "go to leetcode and solve a problem",
            "goal": "Solve LeetCode daily at 6 AM"
        }
        with patch.object(scheduler, "add_schedule") as mock_add:
            mock_add.return_value = {
                "task_id": "test_sched_123",
                "schedule_cron": "Daily 06:00",
                "prompt": "go to leetcode and solve a problem",
                "hour": 6,
                "minute": 0
            }
            ok = await cli.execute_autonomous_step(step, original_line="every day 6 am go to leetcode and solve a problem")
            assert ok is True
            mock_add.assert_called_once()
            call_arg = mock_add.call_args[0][0]
            assert call_arg["hour"] == 6
            assert "leetcode" in call_arg["prompt"].lower()

    async def test_process_directive_schedules_list(self):
        """Verifies direct CLI process_directive routing for 'schedules'."""
        cli = JarvisCLI()
        with patch.object(cli, "list_schedules") as mock_list:
            ok = await cli.process_directive("schedules")
            assert ok is True
            mock_list.assert_called_once()

