"""
Unit and Integration Tests for Modern Next.js Frontend mounted in FastAPI.
Ensures that the Next.js static export at / and /_next are served correctly,
and that all backend endpoints supporting the UI tabs function flawlessly.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
import re

client = TestClient(app)

def test_frontend_root_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    # Verify it is the compiled Next.js bundle
    assert "_next" in response.text

def test_frontend_static_assets_served():
    root_res = client.get("/")
    assert root_res.status_code == 200
    scripts = re.findall(r'src="(/_next/[^"]+)"', root_res.text)
    assert len(scripts) > 0, "No Next.js script tags found in HTML"
    
    # Check that the first static chunk loads with 200 OK
    first_script = scripts[0]
    res = client.get(first_script)
    assert res.status_code == 200
    assert len(res.content) > 0

def test_ui_backend_endpoints():
    # 1. System Health
    h = client.get("/api/health")
    assert h.status_code == 200
    assert h.json()["status"] == "online"

    # 2. Multi-Agent Swarm Telemetry
    t = client.get("/api/agents/telemetry")
    assert t.status_code == 200
    assert "total_cumulative_agents" in t.json()

    # 3. Voice Telephony Roleplay
    v = client.post("/api/voice/roleplay", json={"utterance": "We already have software", "history": []})
    assert v.status_code == 200
    assert "reply" in v.json()

    # 4. REA Binary Audit
    r = client.post("/api/rea/audit", json={"target_path": "main.py"})
    assert r.status_code == 200

    # 5. Hermes Skills Matrix
    s = client.get("/api/hermes/skills")
    assert s.status_code == 200
    assert "skills" in s.json()

    # 6. Hermes Memory Profile
    m = client.get("/api/hermes/memory")
    assert m.status_code == 200
    assert "profile" in m.json()

    # 7. Dynamic Tools List
    tl = client.get("/api/tools/list")
    assert tl.status_code == 200
    assert "tools" in tl.json()

