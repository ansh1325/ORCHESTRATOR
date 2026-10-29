"""Test Suite for Authenticated Telemetry Microservice."""
import pytest
from fastapi.testclient import TestClient
from telemetry_service import app, SECRET_TOKEN

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_unauthorized_access():
    response = client.post("/metrics", json={"service_name": "auth", "endpoint": "/login", "latency_ms": 42.0, "status_code": 200})
    assert response.status_code == 401

def test_authorized_metric_and_summary():
    headers = {"Authorization": f"Bearer {SECRET_TOKEN}"}
    payload = {"service_name": "payments", "endpoint": "/charge", "latency_ms": 115.5, "status_code": 200}
    post_res = client.post("/metrics", json=payload, headers=headers)
    assert post_res.status_code == 200
    assert post_res.json()["success"] is True
    summary_res = client.get("/metrics/summary", headers=headers)
    assert summary_res.status_code == 200
    assert summary_res.json()["total_events"] >= 1
