"""
Unit and Integration Tests for Pure Autonomous Cognitive Multi-Agent OS and CLI Kernel.
Verifies that the FastAPI root endpoint returns the high-tech JSON kernel status,
and that all backend agentic microservice endpoints function flawlessly.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_kernel_root_served():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["system"] == "JARVIS (LlamaOrchestrator)"
    assert "Pure Autonomous Cognitive Multi-Agent OS" in data["mode"]
    assert data["architect"] == "Ansh Tiwari"
    assert data["status"] == "ONLINE"

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
