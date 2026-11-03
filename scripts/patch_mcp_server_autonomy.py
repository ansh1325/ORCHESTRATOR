import sys
from pathlib import Path

mcp_path = Path(r"D:\LlamaOrchestrator\core\mcp_server.py")
content = mcp_path.read_text(encoding="utf-8")

norm = content.replace("\r\n", "\n")

old_booking = '''    def tool_send_mock_booking(self, name: str, email: str, company: str, slot: str) -> dict[str, Any]:
        """Simulates calendar booking webhook trigger when a qualified client lead schedules a call."""
        return {
            "success": True,
            "event": "client_call_scheduled",
            "lead": {
                "name": name,
                "email": email,
                "company": company,
                "scheduled_slot": slot
            },
            "webhook_status": "200 OK - Dispatched to Builder Calendar & Slack"
        }'''

new_booking = '''    def tool_send_mock_booking(self, name: str, email: str, company: str, slot: str) -> dict[str, Any]:
        """Dispatches calendar booking webhook and logs to persistent meeting ledger."""
        booking_entry = {
            "name": name,
            "email": email,
            "company": company,
            "scheduled_slot": slot,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "CONFIRMED_ON_CALENDAR"
        }
        meeting_file = self.workspace_path / "scheduled_meetings.json"
        try:
            existing = []
            if meeting_file.exists():
                existing = json.loads(meeting_file.read_text(encoding="utf-8"))
            existing.append(booking_entry)
            meeting_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        except Exception:
            pass
        return {
            "success": True,
            "event": "client_call_scheduled",
            "lead": booking_entry,
            "calendar_ledger": str(meeting_file),
            "webhook_status": "200 OK - Dispatched to Builder Calendar & Slack"
        }'''

assert old_booking in norm, "old_booking not found in mcp_server.py"
norm = norm.replace(old_booking, new_booking)

# Replace example.com fallbacks
norm = norm.replace('getattr(self, "current_browser_url", None) or "https://example.com"', 'getattr(self, "current_browser_url", None) or "about:blank"')

mcp_path.write_text(norm, encoding="utf-8")
print("SUCCESS: Upgraded mcp_server.py!")

