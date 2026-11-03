"""
Unit & Integration Tests for JARVIS Ambient Visual Streaming Engine
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from PIL import Image
from unittest.mock import MagicMock, patch

from core.ambient_vision import AmbientVisionEngine


def test_frame_hash_and_difference():
    """Verifies perceptual frame hashing and difference calculation."""
    img1 = Image.new("RGB", (320, 180), color=(0, 0, 0))
    img2 = Image.new("RGB", (320, 180), color=(0, 0, 0))
    img3 = Image.new("RGB", (320, 180), color=(255, 255, 255))

    h1 = AmbientVisionEngine.compute_frame_hash(img1)
    h2 = AmbientVisionEngine.compute_frame_hash(img2)
    h3 = AmbientVisionEngine.compute_frame_hash(img3)

    assert h1 == h2
    assert h1 != h3

    diff_identical = AmbientVisionEngine.calculate_frame_difference(img1, img2)
    assert diff_identical == 0.0

    diff_different = AmbientVisionEngine.calculate_frame_difference(img1, img3)
    assert diff_different > 0.9


def test_ambient_frame_capture_and_stream_lifecycle(tmp_path):
    """Verifies ambient frame capture, rolling memory, and start/stop lifecycle."""
    engine = AmbientVisionEngine(sample_interval_seconds=0.1, change_threshold=0.01)
    engine.AMBIENT_DIR = tmp_path

    frame_res = engine.capture_ambient_frame()
    assert "timestamp" in frame_res
    assert "diff_ratio" in frame_res

    # Start and stop stream
    assert engine.start_streaming() is True
    assert engine.get_status()["active"] is True
    assert engine.stop_streaming() is True
    assert engine.get_status()["active"] is False

