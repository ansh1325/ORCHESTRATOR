"""
Unit & Integration Tests for JARVIS Executive Briefing Engine
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from core.executive_briefing import ExecutiveBriefingEngine


def test_executive_briefing_assembly():
    """Verifies that all 5 operational feeds assemble into an executive debrief."""
    report = ExecutiveBriefingEngine.generate_briefing_report()
    assert "formatted_time" in report
    assert "greeting" in report
    assert "hardware" in report
    assert "ports" in report
    assert "git" in report
    assert "fleet" in report
    assert "builds" in report
    assert report["creator"] == "Ansh Tiwari"


def test_format_spoken_briefing():
    """Verifies generation of cinematic 3-bullet spoken speech."""
    report = ExecutiveBriefingEngine.generate_briefing_report()
    spoken = ExecutiveBriefingEngine.format_spoken_briefing(report)
    assert isinstance(spoken, str)
    assert len(spoken) > 50
    assert "Master Ansh" in spoken or "sir" in spoken
    assert "First," in spoken
    assert "Second," in spoken
    assert "Third," in spoken


def test_deliver_briefing_without_crash():
    """Verifies briefing generation and delivery."""
    res = ExecutiveBriefingEngine.deliver_briefing(speak_aloud=False)
    assert "spoken_text" in res
    assert len(res["spoken_text"]) > 0
