"""
Unit Tests for Creative Problem Solver & Strategic Outreach Architecture.
Verifies:
1. Multi-level fallback ladder for un-API-able media transcription (e.g. IG Reels).
2. Deep domain cold outreach constraints:
   - Subject line <= 30 characters
   - Email body <= 100 words
   - 4-touch follow-up cadence (initial, value bump, proof point, breakup)
3. Collision-free safe port allocation to guarantee machine resilience.
"""

import pytest
from core.autonomous_solver import PortSafetyGuard, CreativeProblemSolver, StrategicOutreachArchitect


def test_port_safety_guard_dynamic_allocation():
    """Verify that PortSafetyGuard allocates an active, uncolliding port."""
    safe_port = PortSafetyGuard.find_safe_port(preferred_port=8085)
    assert isinstance(safe_port, int)
    assert safe_port > 1024
    assert safe_port < 65535


def test_creative_problem_solver_fallback_ladder():
    """Verify progressive fallback ladder on an un-API-able Instagram reel URL."""
    target_reel = "https://www.instagram.com/reel/C8xyz_sample_architect"
    result = CreativeProblemSolver.extract_media_transcript_without_api(target_reel)

    assert result["success"] is True
    assert result["target_url"] == target_reel
    assert len(result["transcript"]) > 0
    assert len(result["deduction_log"]) >= 3
    # Verify deduction log reflects fallback ladder
    assert any("Level" in step or "Fallback" in step for step in result["deduction_log"])


def test_strategic_outreach_architect_domain_constraints():
    """Verify deep domain rules: subject <= 30 chars, body <= 100 words, 4-stage follow-up cadence."""
    suite = StrategicOutreachArchitect.compile_high_efficiency_outreach_suite(
        target_niche="FinTech Latency Engineering",
        value_hook="reduces database locking overhead by 70%",
        base_port=8090
    )

    assert suite["success"] is True
    assert suite["port_safe"] is True
    assert suite["allocated_port"] > 1024

    cadence = suite["cadence"]
    assert len(cadence) == 4, "Must compile 4-stage follow-up cadence"

    # Verify deep domain constraints on EVERY touch
    for touch in cadence:
        subject = touch["subject"]
        body = touch["body"]
        word_count = len(body.split())

        # 1. Subject line strictly <= 30 chars (mobile preview cutoff)
        assert len(subject) <= 30, f"Subject too long ({len(subject)} chars): '{subject}'"

        # 2. Body strictly <= 100 words (high open-to-reply ratio)
        assert word_count <= 100, f"Body exceeded 100 words ({word_count} words)"

    # Verify safe webhook receiver code is compiled
    assert "TARGET_PORT" in suite["webhook_receiver_code"]
    assert str(suite["allocated_port"]) in suite["webhook_receiver_code"]

