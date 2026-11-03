"""
Unit & Integration Tests for Hermes Supercharger & Universal Domain Agnosticism.
Verifies that JARVIS operates with:
- Zero brittle hardcoding
- Hermes skill bridge, tiered memory, and proactive cognition
- Proof-of-need lead verification
- Dynamic LeetCode perception and zero 'two-sum' fallbacks
- Autonomous domain adaptability
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.hermes_powerup import hermes_skills, hermes_memory, hermes_cognition
from core.mcp_server import MCPServer
from core.evaluator import EvaluatorGatekeeper
from core.worker import DynamicWorkerEngine
from core.models import SubAgentSpec, TaskNode, KnowledgeBase
from core.orchestrator import SessionState
from core.browser_agent import browser_agent, BrowserElement


def test_hermes_skill_bridge_catalog():
    """Verify that Hermes skills catalog loads and indexes builtin Hermes skills."""
    skills = hermes_skills.list_skills()
    assert len(skills) > 0
    skill_names = [s["name"] for s in skills]
    assert any("email" in n or "research" in n or "dev" in n or "web" in n for n in skill_names)

    # Test filtering
    email_skills = hermes_skills.list_skills(filter_query="email")
    assert len(email_skills) >= 1
    assert "email" in email_skills[0]["name"].lower() or "email" in email_skills[0]["description"].lower()


def test_hermes_tiered_memory_profile_and_episodes(tmp_path):
    """Verify Chief Architect Ansh Tiwari profile, active business goals, and episodic recording."""
    profile = hermes_memory.get_user_profile()
    assert "Ansh Tiwari" in profile.get("name", "")
    assert "Chief Systems Architect" in profile.get("role", "")
    assert profile.get("active_business_goals", {}).get("target_scale") == 1500

    # Test episodic memory recording
    hermes_memory.record_episode(
        goal="Extract 1500 verified tech leads with proof columns",
        outcome="Delivered vetted CSV with RFC-5322 compliance and 4-touch follow-up engine",
        key_deliverables=["leads.csv", "outreach_campaign.py"]
    )
    matches = hermes_memory.search_memories("1500")
    assert len(matches) > 0


def test_hermes_proactive_cognition_vague_prompts():
    """Verify deliberation on vague prompts returns actionable action plans."""
    res = hermes_cognition.deliberate_vague_directive("make me an automated lead engine")
    assert "action_plan" in res or "pipeline" in res or "interpreted_vision" in res


def test_dynamic_mcp_web_search(tmp_path):
    """Verify MCP web search functions without hardcoded static dictionary limitations."""
    mcp = MCPServer(workspace_path=tmp_path)
    res = mcp.tool_web_search("Next.js 15 Server Components and App Router")
    assert res.get("success") is True
    assert "results" in res
    assert len(res["results"]) > 0
    first_res = res["results"][0]
    assert "title" in first_res
    assert "source" in first_res


@pytest.mark.asyncio
async def test_csv_proof_of_need_validation(tmp_path):
    """Verify that evaluator enforces proof-of-need columns when requested in lead generation."""
    mcp = MCPServer(workspace_path=tmp_path)
    evaluator = EvaluatorGatekeeper(mcp=mcp)

    session = SessionState(session_id="test_proof_csv", vision="generate 1500 leads with proof column")

    # 1. Lead CSV with proof column
    valid_csv = "Name,Email,Company,Role,Status,Verified,ProofOfNeed,ObservedSignal\nAlex,alex@tech.co,Tech Co,CTO,Valid,Yes,Hiring backend engineers,High\n"
    mcp.tool_file_write("leads.csv", valid_csv)

    eval_res = await evaluator.evaluate_deliverables(
        session_id="test_proof_csv",
        track_type="business_acquisition",
        session=session
    )
    proof_checks = [c for c in eval_res.get("checks", []) if "Proof Column" in c.get("check", "")]
    assert len(proof_checks) == 1
    assert proof_checks[0]["passed"] is True

    # 2. Lead CSV missing proof column
    invalid_csv = "Name,Email,Company,Role,Status,Verified\nAlex,alex@tech.co,Tech Co,CTO,Valid,Yes\n"
    mcp.tool_file_write("leads_no_proof.csv", invalid_csv)
    eval_res2 = await evaluator.evaluate_deliverables(
        session_id="test_proof_csv",
        track_type="business_acquisition",
        session=session
    )
    no_proof_checks = [c for c in eval_res2.get("checks", []) if "Proof Column" in c.get("check", "") and "leads_no_proof.csv" in c.get("check", "")]
    assert len(no_proof_checks) == 1
    assert no_proof_checks[0]["passed"] is False


@pytest.mark.asyncio
async def test_worker_fallback_includes_proof_columns(tmp_path):
    """Verify that DynamicWorkerEngine produces CSV deliverables containing proof columns."""
    mcp = MCPServer(workspace_path=tmp_path)
    worker = DynamicWorkerEngine(mcp=mcp)

    task = TaskNode(
        id="task_lead_gen",
        title="Scrape and structure decision maker leads into CSV",
        agent_type="LeadScraperAgent",
        description="Extract prospect leads into leads.csv with proof-of-need observation"
    )
    spec = SubAgentSpec(
        agent_id="agent_lead",
        name="Lead Engineer",
        role="Lead Generation Specialist",
        system_prompt="Harvest verified leads into CSV.",
        allowed_tools=["file_write", "file_read"]
    )

    artifacts = await worker._perform_subagent_work(task, spec, track_type="business_acquisition", attempt=0)
    assert "leads.csv" in artifacts

    content = mcp.tool_file_read("leads.csv")["content"]
    header = content.splitlines()[0]
    assert "ProofOfNeed" in header
    assert "ObservedSignal" in header


def test_leetcode_no_hardcoded_two_sum():
    """Verify that browser_agent code contains zero hardcoded two-sum redirections in solver."""
    import inspect
    solver_source = inspect.getsource(browser_agent.solve_leetcode_problem)
    assert 'target_url = "https://leetcode.com/problems/two-sum/"' not in solver_source
    assert 'page.goto("https://leetcode.com/problems/two-sum/"' not in solver_source
    # Verify dynamic catalog and dynamic random question redirect are present
    assert 'https://leetcode.com/problemset/' in solver_source
    assert 'https://leetcode.com/problems/random-one-question/' in solver_source
