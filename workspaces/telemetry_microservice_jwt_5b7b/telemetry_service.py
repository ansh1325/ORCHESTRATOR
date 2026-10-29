"""Authenticated Telemetry Microservice."""
import time
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI(title="Authenticated Telemetry Service", version="1.0.0")
security = HTTPBearer()
SECRET_TOKEN = "llama-secret-bearer-token-2026"
metrics_db: List[Dict[str, Any]] = []

class TelemetryPayload(BaseModel):
    service_name: str
    endpoint: str
    latency_ms: float
    status_code: int

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != SECRET_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    return credentials.credentials

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "telemetry-engine"}

@app.post("/metrics")
def record_metric(payload: TelemetryPayload, token: str = Depends(verify_token)):
    record = payload.model_dump()
    record["recorded_at"] = time.time()
    metrics_db.append(record)
    return {"success": True, "total_records": len(metrics_db)}

@app.get("/metrics/summary")
def get_summary(token: str = Depends(verify_token)):
    count = len(metrics_db)
    avg_lat = sum(m["latency_ms"] for m in metrics_db) / max(1, count)
    return {"total_events": count, "average_latency_ms": round(avg_lat, 2)}
