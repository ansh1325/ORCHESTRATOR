"""
Unit & Integration Tests for Founder Mode & Unbounded Agent Swarm Engine
"""

from core.founder_engine import FounderInterviewEngine
from core.orchestrator import MetaOrchestrator

def test_founder_interview_generation():
    vision = "build me an AI lead intelligence tool that finds seed SaaS founders and drafts pull requests"
    questions = FounderInterviewEngine.generate_founder_interview(vision)
    
    assert len(questions) == 4
    q_ids = [q.id for q in questions]
    assert "target_audience_and_pain_point" in q_ids
    assert "software_architecture_pattern" in q_ids
    assert "continuous_schedule_cadence" in q_ids
    assert "deliverable_package_format" in q_ids

def test_unbounded_agent_swarm_compilation():
    vision = "automated stock arbitrage bot and daily email digest"
    plan = FounderInterviewEngine.compile_unbounded_agent_swarm(
        session_id="test_founder_swarm",
        vision=vision,
        answers={}
    )
    
    assert len(plan.nodes) == 8
    node_ids = [n.id for n in plan.nodes]
    assert "task_01_spec_architect" in node_ids
    assert "task_02_data_engine" in node_ids
    assert "task_03_core_logic" in node_ids
    assert "task_04_persistence" in node_ids
    assert "task_05_browser_automator" in node_ids
    assert "task_06_continuous_daemon" in node_ids
    assert "task_07_pytest_suite" in node_ids
    assert "task_08_runbook_docs" in node_ids

def test_orchestrator_founder_mode_routing():
    orch = MetaOrchestrator()
    vision = "I want to build a creator business intelligence tool that monitors competitor pricing daily"
    
    analysis = orch.analyze_intent(vision, session_id="test_founder_routing")
    assert analysis.track_type == "founder_software"
    assert "Unbounded Founder Swarm" in analysis.swarm_size_descriptor
    
    plan = orch.compile_dag_plan(session_id="test_founder_routing")
    assert len(plan.nodes) >= 6

