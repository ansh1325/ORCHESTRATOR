"""
LlamaOrchestrator 24/7 Autonomous Background Scheduler Engine
Runs persistently on the host PC to execute recurring missions at designated times (e.g. Daily 6:00 AM).
Maintains schedules in schedules.json and integrates with MetaOrchestrator for background compilation.
"""

import re
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from core.config import settings

SCHEDULES_FILE = settings.WORKSPACE_DIR / "schedules.json"

def parse_schedule_directive(text: str) -> Optional[Dict[str, Any]]:
    """
    Detects recurring daily schedule commands like:
    - 'everyday at 6am'
    - 'daily at 06:00'
    - 'every morning at 7:30 am'
    - 'schedule this for everyday at 6am: ...'
    """
    if not text:
        return None
    pattern = r"(?:every\s*day|daily|every\s*morning|every\s*night)\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        pattern2 = r"schedule\s+(?:this\s+)?(?:for\s+)?(?:every\s*day|daily)?\s*at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
        m = re.search(pattern2, text, re.IGNORECASE)
        if not m:
            return None

    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    meridiem = (m.group(3) or "").lower()
    if meridiem == "pm" and hour < 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0

    cleaned_prompt = re.sub(pattern, "", text, flags=re.IGNORECASE)
    cleaned_prompt = re.sub(
        r"^(?:do\s+this\s+particular\s+work\s+for|do\s+this\s+for|schedule\s+this\s+for|please\s+run\s+this)\s*",
        "",
        cleaned_prompt,
        flags=re.IGNORECASE
    ).strip(" :,-")
    if not cleaned_prompt:
        cleaned_prompt = text

    words = re.findall(r'[a-zA-Z0-9@.-]+', cleaned_prompt)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'of', 'on', 'with', 'at', 'by', 'from', 'as', 'is', 'it', 'all', 'be', 'will', 'that', 'this'}
    meaningful = [w.capitalize() for w in words if w.lower() not in stop_words]
    title_suffix = " ".join(meaningful[:4]) if meaningful else cleaned_prompt[:30]

    title = f"Daily {hour:02d}:{minute:02d} - {title_suffix}"
    return {
        "hour": hour,
        "minute": minute,
        "schedule_cron": f"Daily {hour:02d}:{minute:02d}",
        "prompt": cleaned_prompt,
        "title": title
    }

class AutonomousScheduler:
    """Manages persistent recurring tasks and coordinates background execution."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or settings.WORKSPACE_DIR
        self._ensure_file()

    def _ensure_file(self):
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        s_file = self.workspace_dir / "schedules.json"
        if not s_file.exists():
            with open(s_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def list_schedules(self) -> List[Dict[str, Any]]:
        s_file = self.workspace_dir / "schedules.json"
        try:
            with open(s_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def add_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        schedules = self.list_schedules()
        task_id = schedule_data.get("task_id") or schedule_data.get("id") or f"sched_{uuid.uuid4().hex[:8]}"
        hour = int(schedule_data.get("hour", 6))
        minute = int(schedule_data.get("minute", 0))
        sched_time = schedule_data.get("schedule_cron") or f"Daily {hour:02d}:{minute:02d}"

        entry = {
            "task_id": task_id,
            "id": task_id,
            "title": schedule_data.get("title") or "Daily Autonomous Mission",
            "prompt": schedule_data.get("prompt", ""),
            "schedule_cron": sched_time,
            "hour": hour,
            "minute": minute,
            "is_active": schedule_data.get("is_active", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run_at": None,
            "last_run_date": None,
            "run_count": 0
        }

        existing = False
        for i, s in enumerate(schedules):
            if s.get("task_id") == task_id or s.get("id") == task_id:
                schedules[i] = entry
                existing = True
                break
        if not existing:
            schedules.append(entry)

        self._save_schedules(schedules)
        return entry

    def toggle_schedule(self, task_id: str, is_active: bool) -> bool:
        schedules = self.list_schedules()
        for s in schedules:
            if s.get("task_id") == task_id or s.get("id") == task_id:
                s["is_active"] = is_active
                self._save_schedules(schedules)
                return True
        return False

    def delete_schedule(self, task_id: str) -> bool:
        schedules = self.list_schedules()
        filtered = [s for s in schedules if s.get("task_id") != task_id and s.get("id") != task_id]
        if len(filtered) != len(schedules):
            self._save_schedules(filtered)
            return True
        return False

    def update_schedule_run_status(self, task_id: str, run_date_str: str):
        schedules = self.list_schedules()
        for s in schedules:
            if s.get("task_id") == task_id or s.get("id") == task_id:
                s["last_run_at"] = datetime.now(timezone.utc).isoformat()
                s["last_run_date"] = run_date_str
                s["run_count"] = int(s.get("run_count", 0)) + 1
                self._save_schedules(schedules)
                break

    def _save_schedules(self, schedules: List[Dict[str, Any]]):
        s_file = self.workspace_dir / "schedules.json"
        try:
            with open(s_file, "w", encoding="utf-8") as f:
                json.dump(schedules, f, indent=2)
        except Exception:
            pass

    async def autonomous_scheduler_daemon(self, orchestrator_instance: Any, poll_interval_sec: int = 25):
        """Infinite background loop checking scheduled tasks and triggering execution."""
        while True:
            try:
                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute
                today_str = now.strftime("%Y-%m-%d")

                schedules = self.list_schedules()
                for sched in schedules:
                    if not sched.get("is_active", True):
                        continue
                    s_hour = int(sched.get("hour", 6))
                    s_minute = int(sched.get("minute", 0))

                    if current_hour == s_hour and current_minute == s_minute:
                        if sched.get("last_run_date") != today_str:
                            tid = sched.get("task_id") or sched.get("id") or "sched"
                            print(f"[Scheduler] ⏰ Triggering scheduled daily mission '{sched.get('title')}' at {now.strftime('%H:%M:%S')}...")
                            self.update_schedule_run_status(tid, today_str)
                            asyncio.create_task(
                                orchestrator_instance.run_scheduled_mission(
                                    prompt=sched.get("prompt", ""),
                                    title=sched.get("title", "Daily Autonomous Mission")
                                )
                            )
            except Exception as e:
                print(f"[Scheduler Loop Error] {e}")
            await asyncio.sleep(poll_interval_sec)

# Global Singleton Scheduler
scheduler = AutonomousScheduler()

