"""
LlamaOrchestrator Workflow & History Management Engine
Encapsulates persistent mission history, chat pinning, folder categorization,
and reusable workflow blueprints.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.config import settings

HISTORY_FILE = settings.WORKSPACE_DIR / "history.json"
WORKFLOWS_FILE = settings.WORKSPACE_DIR / "workflows.json"

DEFAULT_WORKFLOWS: list[dict[str, Any]] = [
    {
        "id": "wf_emails",
        "title": "3 Personal Emails from Jarvis",
        "description": "Drafts 3 heartfelt loyalty emails to anshtiwarisocial@gmail.com with subject 'hello i am jarvis'.",
        "prompt_template": "HEy just write me 3 mails to mail address anshtiwarisocial@gmail.com just subject line hello i am jarvis and body with whatever you feel for me",
        "folder": "Personal"
    },
    {
        "id": "wf_agency",
        "title": "Client-Acquisition Agency Business",
        "description": "Scaffolds complete B2B agency, scrapes leads, and simulates calendar bookings.",
        "prompt_template": "I know full-stack dev, build me a business and find me clients",
        "folder": "Business"
    },
    {
        "id": "wf_telemetry",
        "title": "Authenticated Telemetry Microservice",
        "description": "Compiles production FastAPI telemetry service with JWT auth and 100% Pytest pass.",
        "prompt_template": "Build an authenticated telemetry microservice with JWT & tests",
        "folder": "Engineering"
    }
]

class WorkflowAndHistoryManager:
    """Manages persistent work history, folders, pins, and saved workflows."""

    def __init__(self, workspace_dir: Path | None = None):
        self.workspace_dir = workspace_dir or settings.WORKSPACE_DIR
        self._ensure_files()

    def _ensure_files(self):
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        h_file = self.workspace_dir / "history.json"
        w_file = self.workspace_dir / "workflows.json"
        if not h_file.exists():
            with open(h_file, "w", encoding="utf-8") as f:
                json.dump([], f)
        if not w_file.exists():
            with open(w_file, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_WORKFLOWS, f, indent=2)

    def list_history(self) -> list[dict[str, Any]]:
        h_file = self.workspace_dir / "history.json"
        try:
            with open(h_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            # Pinned missions appear at the top, followed by newest created_at
            items.sort(key=lambda x: (1 if x.get("is_pinned") else 0, x.get("created_at", "")), reverse=True)
            return items
        except Exception:
            return []

    get_history = list_history

    def record_session(
        self,
        session_id: str,
        title: str,
        prompt: str,
        folder: str = "General",
        artifacts: list[str] | None = None
    ):
        history = self.list_history()
        # Update if exists, else prepend
        for item in history:
            if item.get("session_id") == session_id:
                item["title"] = title
                item["artifacts"] = artifacts or []
                item["deliverables"] = artifacts or []
                item["status"] = "completed"
                self._save_history(history)
                return
        new_item = {
            "session_id": session_id,
            "title": title,
            "prompt": prompt,
            "folder": folder,
            "is_pinned": False,
            "status": "completed",
            "created_at": datetime.now(UTC).isoformat(),
            "artifacts": artifacts or [],
            "deliverables": artifacts or []
        }
        history.insert(0, new_item)
        self._save_history(history)

    def update_folder(self, session_id: str, folder: str):
        history = self.list_history()
        for item in history:
            if item.get("session_id") == session_id:
                item["folder"] = folder
                break
        self._save_history(history)

    def toggle_pin(self, session_id: str, is_pinned: bool):
        history = self.list_history()
        for item in history:
            if item.get("session_id") == session_id:
                item["is_pinned"] = is_pinned
                break
        self._save_history(history)

    def delete_session(self, session_id: str) -> bool:
        history = self.list_history()
        initial_len = len(history)
        history = [item for item in history if item.get("session_id") != session_id]
        if len(history) < initial_len:
            self._save_history(history)
            return True
        return False

    def _save_history(self, history: list[dict[str, Any]]):
        h_file = self.workspace_dir / "history.json"
        try:
            with open(h_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def list_workflows(self) -> list[dict[str, Any]]:
        w_file = self.workspace_dir / "workflows.json"
        try:
            with open(w_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_WORKFLOWS

    def save_workflow(self, workflow_data: dict[str, Any]):
        wfs = self.list_workflows()
        import uuid
        wf_id = workflow_data.get("id") or f"wf_{uuid.uuid4().hex[:8]}"
        workflow_data["id"] = wf_id
        if "title" not in workflow_data and "name" in workflow_data:
            workflow_data["title"] = workflow_data["name"]
        if "prompt_template" not in workflow_data and "prompt" in workflow_data:
            workflow_data["prompt_template"] = workflow_data["prompt"]
        if "folder" not in workflow_data and "category" in workflow_data:
            workflow_data["folder"] = workflow_data["category"]

        existing_idx = next((i for i, w in enumerate(wfs) if w.get("id") == wf_id or (w.get("title") and w.get("title") == workflow_data.get("title"))), -1)
        if existing_idx >= 0:
            wfs[existing_idx] = workflow_data
        else:
            wfs.append(workflow_data)

        w_file = self.workspace_dir / "workflows.json"
        try:
            with open(w_file, "w", encoding="utf-8") as f:
                json.dump(wfs, f, indent=2)
        except Exception:
            pass

    def delete_workflow(self, workflow_id: str) -> bool:
        wfs = self.list_workflows()
        filtered = [w for w in wfs if w.get("id") != workflow_id and w.get("name") != workflow_id]
        if len(filtered) != len(wfs):
            w_file = self.workspace_dir / "workflows.json"
            try:
                with open(w_file, "w", encoding="utf-8") as f:
                    json.dump(filtered, f, indent=2)
                return True
            except Exception:
                pass
        return False

    # Scheduler Delegators for seamless modular access
    def list_schedules(self) -> list[dict[str, Any]]:
        from core.scheduler import scheduler  # pyright: ignore[reportMissingImports]
        return scheduler.list_schedules()

    def add_schedule(self, schedule_data: dict[str, Any]) -> dict[str, Any]:
        from core.scheduler import scheduler  # pyright: ignore[reportMissingImports]
        return scheduler.add_schedule(schedule_data)

    def toggle_schedule(self, task_id: str, is_active: bool) -> bool:
        from core.scheduler import scheduler  # pyright: ignore[reportMissingImports]
        return scheduler.toggle_schedule(task_id, is_active)

    def delete_schedule(self, task_id: str) -> bool:
        from core.scheduler import scheduler  # pyright: ignore[reportMissingImports]
        return scheduler.delete_schedule(task_id)

    def update_schedule_run_status(self, task_id: str, run_date_str: str):
        from core.scheduler import scheduler  # pyright: ignore[reportMissingImports]
        scheduler.update_schedule_run_status(task_id, run_date_str)

# Global Singleton Manager
workflow_manager = WorkflowAndHistoryManager()
# Alias for backwards compatibility
HistoryManager = WorkflowAndHistoryManager
history_manager = workflow_manager
