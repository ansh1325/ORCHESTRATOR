# Telemetry Database Models & Schema (SQLAlchemy / SQLite)
from datetime import datetime
from pydantic import BaseModel, Field

class MetricRecord(BaseModel):
    id: int
    service_name: str
    endpoint: str
    latency_ms: float
    status_code: int
    timestamp: str
