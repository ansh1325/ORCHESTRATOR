"""
Unit & Integration Tests for Real Browser Controller & Dispatch Endpoints
"""

from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from core.browser_controller import BrowserController

client = TestClient(app)

def test_build_gmail_compose_url():
    url = BrowserController.build_gmail_compose_url(
        recipient="anshtiwarisocial@gmail.com",
        subject="hello i am jarvis",
        body="Dear Ansh, test letter."
    )
    assert url.startswith("https://mail.google.com/mail/?view=cm")
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
