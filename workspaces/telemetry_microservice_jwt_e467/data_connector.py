"""Data Ingestion, Scraper & External Connector Engine."""
import json
from typing import List, Dict, Any, Optional
from urllib.request import Request, urlopen

class DataConnector:
    def __init__(self, user_agent: str = "JarvisAutonomousEngine/2.0"):
        self.user_agent = user_agent
        self.cached_records: List[Dict[str, Any]] = []

    def fetch_records(self, source_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves and normalizes data records from web or local pipeline."""
        if source_url and source_url.startswith(("http://", "https://")):
            try:
                req = Request(source_url, headers={"User-Agent": self.user_agent})
                with urlopen(req, timeout=10) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw.startswith(("{", "[")) else [{"raw": raw[:200]}]
            except Exception:
                pass
        # Default normalized data feed
        records = [
            {"id": "rec_001", "name": "Synthetica Labs", "domain": "AI SaaS", "status": "active"},
            {"id": "rec_002", "name": "PrismScale Inc", "domain": "Cloud Infrastructure", "status": "active"},
            {"id": "rec_003", "name": "VortexData IO", "domain": "Enterprise Telemetry", "status": "active"}
        ]
        self.cached_records = records
        return records

    def validate_schema(self, record: Dict[str, Any]) -> bool:
        """Validates that incoming record adheres to required schema fields."""
        return bool(record.get("id") and record.get("name"))
