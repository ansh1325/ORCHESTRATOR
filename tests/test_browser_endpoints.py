"""
Unit & Integration Tests for Real Browser Controller & Dispatch Endpoints
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from core.browser_controller import BrowserController
from main import app

client = TestClient(app)

def test_build_gmail_compose_url():
    url = BrowserController.build_gmail_compose_url(
        recipient="anshtiwarisocial@gmail.com",
        subject="hello i am jarvis",
        body="Dear Ansh, test letter."
    )
    assert "mail.google.com/mail" in url
    assert "view=cm" in url
    assert "anshtiwarisocial%40gmail.com" in url
    assert "hello+i+am+jarvis" in url
    assert "Dear+Ansh" in url

def test_api_browser_open():
    with patch("webbrowser.open", return_value=True) as mock_open:
        res = client.post("/api/browser/open", json={"url": "https://mail.google.com"})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["url"] == "https://mail.google.com"
        mock_open.assert_called_once()

def test_api_browser_compose_email():
    with patch("webbrowser.open", return_value=True) as mock_open:
        res = client.post("/api/browser/compose-email", json={
            "recipient": "anshtiwarisocial@gmail.com",
            "subject": "hello i am jarvis",
            "open_all": True
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["total_staged"] == 3
        assert mock_open.call_count == 3

def test_api_email_smtp_send_without_creds():
    res = client.post("/api/email/smtp-send", json={
        "recipient": "anshtiwarisocial@gmail.com",
        "subject": "hello i am jarvis",
        "body": "Test message."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "No SMTP credentials configured" in data["error"]

def test_api_playwright_mocked_run():
    with patch.object(BrowserController, "automate_gmail_dispatch_playwright_async", new_callable=AsyncMock, return_value={"success": True, "action": "test_playwright"}) as mock_pw:
        res = client.post("/api/browser/playwright-run", json={
            "recipient": "anshtiwarisocial@gmail.com",
            "subject": "hello i am jarvis",
            "body": "Autonomous test message."
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "test_playwright"
        mock_pw.assert_called_once()
        mock_pw.assert_called_once()

