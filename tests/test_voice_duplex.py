"""
Unit & Integration Tests for JARVIS Streaming Voice Duplex with Acoustic Barge-In
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from unittest.mock import MagicMock, patch

from core.voice_duplex import VoiceDuplexEngine, VoiceSynthesizer, DuplexState


def test_voice_synthesizer_initialization():
    """Verifies that native Windows SAPI voice synthesizer initializes."""
    synth = VoiceSynthesizer()
    assert synth is not None
    # Test async speak
    res = synth.speak_async("Test vocalization")
    assert res is True
    # Test acoustic barge-in interruption (purge)
    assert synth.interrupt() is True


def test_acoustic_barge_in_interruption():
    """
    Verifies that when JARVIS is speaking and user starts talking,
    acoustic barge-in halts speech immediately and resets state.
    """
    duplex = VoiceDuplexEngine()
    duplex.state = DuplexState.SPEAKING

    # Simulate user speaking with energy exceeding threshold
    event = duplex.handle_incoming_audio_chunk(
        audio_bytes=b"RIFF" + b"\x00" * 300,
        energy_level=0.9
    )

    assert event["barge_in_triggered"] is True
    assert duplex.barge_in_count >= 1
    assert event["reply_spoken"] is True


def test_voice_duplex_session_lifecycle():
    """Verifies session start, stop, and telemetry inspection."""
    duplex = VoiceDuplexEngine()
    assert duplex.state == DuplexState.IDLE

    # Start session
    duplex.start_duplex_session()
    assert duplex.state == DuplexState.LISTENING

    telem = duplex.get_telemetry()
    assert telem["active"] is True
    assert "state" in telem

    # Stop session
    duplex.stop_duplex_session()
    assert duplex.state == DuplexState.IDLE
