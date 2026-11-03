"""
Unit & Integration Tests for JARVIS Stark Voice Identity & Acoustic Stylist
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from core.voice_identity import StarkPersona, VoiceIdentityEngine


def test_stark_persona_text_cleaner():
    """Verifies that markdown, URLs, and code blocks are cleaned for speech."""
    raw = "### Header\nHere is a `var_name` and a [link](https://example.com). Also **bold**."
    clean = StarkPersona.clean_text_for_speech(raw)
    assert "#" not in clean
    assert "`" not in clean
    assert "https://" not in clean
    assert "*" not in clean
    assert "var name" in clean or "var_name" in clean
    assert "bold" in clean


def test_stark_persona_dialogue_styling():
    """Verifies time-aware greeting and task confirmations."""
    morning = StarkPersona.style_greeting(hour=9)
    assert "Good morning" in morning
    assert "Master Ansh" in morning

    evening = StarkPersona.style_greeting(hour=20)
    assert "Good evening" in evening

    confirm = StarkPersona.style_confirmation("compiling microservice")
    assert "Right away, sir" in confirm

    complete = StarkPersona.style_completion("Lead Hunting Campaign", "14 leads verified")
    assert "Objective accomplished" in complete
    assert "14 leads verified" in complete


def test_voice_identity_speak_and_interrupt():
    """Verifies voice identity speak execution and acoustic barge-in."""
    engine = VoiceIdentityEngine()
    res = engine.speak("Status check, Master Ansh.")
    assert res is True
    assert engine.interrupt() is True
