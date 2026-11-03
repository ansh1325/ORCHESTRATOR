"""
Unit & Integration Tests for JARVIS Autonomous Anti-Bot & CAPTCHA Defense Engine
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from unittest.mock import MagicMock, patch

from core.captcha_solver import CaptchaSolver
from core.browser_controller import BrowserController


def test_stealth_script_injection():
    """Verifies that stealth JavaScript evasions are injected into the page."""
    mock_page = MagicMock()
    res = CaptchaSolver.apply_stealth_to_page(mock_page)
    assert res is True
    assert mock_page.add_init_script.called or mock_page.evaluate.called
    injected = mock_page.add_init_script.call_args[0][0]
    assert "navigator.webdriver" in injected
    assert "window.chrome" in injected


def test_transcribe_audio_bytes_fallback():
    """Verifies audio buffer transcription handling."""
    dummy_bytes = b"ID3" + b"\x00" * 200
    res = CaptchaSolver.transcribe_audio_bytes(dummy_bytes)
    assert isinstance(res, str)
    assert len(res) > 0


def test_turnstile_cloudflare_autonomous_solve():
    """Verifies autonomous Turnstile detection and human Bezier click resolution."""
    mock_page = MagicMock()
    mock_frame = MagicMock()
    mock_frame.url = "https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/g/turnstile"

    mock_cb = MagicMock()
    mock_cb.count.return_value = 1
    mock_cb.is_visible.return_value = True
    mock_cb.bounding_box.return_value = {"x": 100, "y": 200, "width": 50, "height": 30}

    mock_frame.locator.return_value.first = mock_cb
    mock_page.frames = [mock_frame]

    res = CaptchaSolver.solve_turnstile_cloudflare(mock_page)
    assert res["detected"] is True
    assert res["solved"] is True
    assert mock_page.mouse.move.called
    assert mock_page.mouse.down.called
    assert mock_page.mouse.up.called


def test_recaptcha_v2_audio_whisper_bypass():
    """Verifies autonomous reCAPTCHA v2 audio challenge interception and Whisper bypass."""
    mock_page = MagicMock()
    
    # 1. Anchor Frame (Checkbox)
    anchor_frame = MagicMock()
    anchor_frame.url = "https://www.google.com/recaptcha/api2/anchor"
    mock_rc_box = MagicMock()
    mock_rc_box.count.return_value = 1
    mock_rc_box.is_visible.return_value = True
    mock_rc_box.bounding_box.return_value = {"x": 50, "y": 50, "width": 28, "height": 28}
    anchor_frame.locator.return_value.first = mock_rc_box

    # 2. Challenge BFrame
    bframe = MagicMock()
    bframe.url = "https://www.google.com/recaptcha/api2/bframe"
    
    audio_btn = MagicMock()
    audio_btn.count.return_value = 1
    audio_btn.is_visible.return_value = True
    audio_btn.bounding_box.return_value = {"x": 80, "y": 300, "width": 20, "height": 20}

    dl_link = MagicMock()
    dl_link.count.return_value = 1
    dl_link.get_attribute.return_value = "https://www.google.com/recaptcha/api2/payload/audio.mp3"

    input_box = MagicMock()
    input_box.count.return_value = 1

    verify_btn = MagicMock()
    verify_btn.count.return_value = 1
    verify_btn.bounding_box.return_value = {"x": 120, "y": 350, "width": 60, "height": 30}

    def bframe_locator(sel):
        m = MagicMock()
        if "audio-button" in sel:
            m.first = audio_btn
        elif "download-link" in sel:
            m.first = dl_link
        elif "audio-response" in sel or "response-input" in sel:
            m.first = input_box
        elif "verify-button" in sel:
            m.first = verify_btn
        else:
            m.first = MagicMock(count=lambda: 0)
        return m

    bframe.locator.side_effect = bframe_locator
    mock_page.frames = [anchor_frame, bframe]

    with patch("urllib.request.urlopen") as mock_url:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"RIFF" + b"\x00" * 500
        mock_resp.__enter__.return_value = mock_resp
        mock_url.return_value = mock_resp

        res = CaptchaSolver.solve_recaptcha_v2_audio(mock_page)

    assert res["detected"] is True
    assert res["solved"] is True
    assert input_box.fill.called


def test_browser_controller_delegates_to_captcha_solver():
    """Verifies that BrowserController.defeat_or_detect_captcha coordinates with CaptchaSolver."""
    mock_page = MagicMock()
    mock_frame = MagicMock()
    mock_frame.url = "https://challenges.cloudflare.com/turnstile"
    mock_cb = MagicMock()
    mock_cb.count.return_value = 1
    mock_cb.is_visible.return_value = True
    mock_cb.bounding_box.return_value = {"x": 10, "y": 20, "width": 30, "height": 30}
    mock_frame.locator.return_value.first = mock_cb
    mock_page.frames = [mock_frame]

    res = BrowserController.defeat_or_detect_captcha(mock_page)
    assert res.get("detected") is True
    assert res.get("solved_autonomously") is True
