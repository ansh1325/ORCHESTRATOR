"""
LlamaOrchestrator 24/7 Autonomous Background Scheduler Engine
Runs persistently on the host PC to execute recurring missions at designated times (e.g. Daily 6:00 AM).
Maintains schedules in schedules.json and integrates with MetaOrchestrator for background compilation.
"""

import asyncio
import json
import os
import re
import sys
import uuid
import subprocess
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from core.config import settings

logger = logging.getLogger("Jarvis.Scheduler")

SCHEDULES_FILE = settings.WORKSPACE_DIR / "schedules.json"

def parse_schedule_directive(text: str) -> dict[str, Any] | None:
    """
    Detects recurring daily, continuous, or time-based schedule directives:
    - 'every day 6 am go to leetcode and solve a problem'
    - 'daily at 06:00 check crypto portfolio'
    - 'every morning 7:30 am check emails'
    - 'at 6 am everyday commit to github'
    - 'continuous non ending workflows'
    - 'run continuously 24/7'
    - 'every hour'
    """
    if not text:
        return None

    # Immediate or one-off tasks are not recurring schedules unless explicitly requesting a scheduled time
    if re.search(r'\b(?:today|tonight|right now|now|immediately|once)\b', text, re.IGNORECASE):
        if not re.search(r'\b(?:every|daily|continuously|24/7|hourly|schedule)\b', text, re.IGNORECASE):
            return None


    # 1. Continuous Non-Ending Loop Directives
    if re.search(r"\b(?:continuously|continuous|non-?ending|24/7|forever|perpetual|unending)\b", text, re.IGNORECASE):
        cleaned_prompt = re.sub(r"\b(?:continuously|continuous non-?ending workflows?|continuous workflows?|run continuously|24/7|non-?ending)\b", "", text, flags=re.IGNORECASE).strip(" :,-")
        if not cleaned_prompt:
            cleaned_prompt = text
        words = re.findall(r'[a-zA-Z0-9@.-]+', cleaned_prompt)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'of', 'on', 'with', 'at', 'by', 'from', 'as', 'is', 'it', 'all', 'be', 'will', 'that', 'this'}
        meaningful = [w.capitalize() for w in words if w.lower() not in stop_words]
        title_suffix = " ".join(meaningful[:4]) if meaningful else cleaned_prompt[:30]
        return {
            "hour": -1,
            "minute": -1,
            "schedule_cron": "Continuous (24/7 Daemon Loop)",
            "prompt": cleaned_prompt,
            "title": f"Continuous 24/7 - {title_suffix}"
        }

    # 2. Hourly Cadence
    if re.search(r"\b(?:every\s*hour|hourly)\b", text, re.IGNORECASE):
        cleaned_prompt = re.sub(r"\b(?:every\s*hour|hourly)\b", "", text, flags=re.IGNORECASE).strip(" :,-")
        if not cleaned_prompt:
            cleaned_prompt = text
        words = re.findall(r'[a-zA-Z0-9@.-]+', cleaned_prompt)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'of', 'on', 'with', 'at', 'by', 'from', 'as', 'is', 'it', 'all', 'be', 'will', 'that', 'this'}
        meaningful = [w.capitalize() for w in words if w.lower() not in stop_words]
        title_suffix = " ".join(meaningful[:4]) if meaningful else cleaned_prompt[:30]
        return {
            "hour": -1,
            "minute": 0,
            "schedule_cron": "Hourly (:00)",
            "prompt": cleaned_prompt,
            "title": f"Hourly - {title_suffix}"
        }

    # 3. Flexible Daily / Specific Time Patterns
    pattern1 = r"\b(?:every\s*day|daily|every\s*morning|every\s*night|every\s*evening|everyday)\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b"
    pattern2 = r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+(?:every\s*day|daily|every\s*morning|every\s*night|everyday)\b"
    pattern3 = r"\bschedule\s+(?:this\s+)?(?:for\s+)?(?:every\s*day|daily)?\s*(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b"

    m = re.search(pattern1, text, re.IGNORECASE) or re.search(pattern2, text, re.IGNORECASE) or re.search(pattern3, text, re.IGNORECASE)

    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        meridiem = (m.group(3) or "").lower()
        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0

        # Remove the matched schedule timing clause from prompt
        cleaned_prompt = (text[:m.start()] + text[m.end():]).strip(" :,-")
        cleaned_prompt = re.sub(
            r"^(?:schedule\s+(?:this\s+)?(?:for\s+)?|do\s+this\s+particular\s+work\s+for|do\s+this\s+for|please\s+run\s+this)\s*",
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

    # 4. Cognitive LLM Fallback for Unorthodox Natural Phrasing
    try:
        llm = settings.get_llm_client()
        if llm and not settings.is_mock():
            prompt = (
                "Analyze if this user text requests a scheduled or recurring task.\n"
                f"Directive: \"{text}\"\n\n"
                "If it does, extract the frequency ('daily', 'hourly', 'continuous'), hour (0-23 in 24hr format), "
                "minute (0-59), and the action prompt with timing words removed.\n"
                "If not a schedule request, output {\"is_scheduled\": false}.\n"
                "Output strictly JSON: {\"is_scheduled\": true, \"hour\": 6, \"minute\": 0, \"schedule_cron\": \"Daily 06:00\", \"prompt\": \"...\", \"title\": \"...\"}"
            )
            resp = settings.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are JARVIS Schedule Parser. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            if data.get("is_scheduled"):
                return {
                    "hour": int(data.get("hour", 6)),
                    "minute": int(data.get("minute", 0)),
                    "schedule_cron": str(data.get("schedule_cron", "Daily 06:00")),
                    "prompt": str(data.get("prompt") or text).strip(),
                    "title": str(data.get("title") or f"Scheduled: {text[:30]}")
                }
    except Exception:
        pass

    return None

class AutonomousScheduler:
    """Manages persistent recurring tasks and coordinates background execution."""

    def __init__(self, workspace_dir: Path | None = None):
        self.workspace_dir = workspace_dir or settings.WORKSPACE_DIR
        self._ensure_file()

    def _ensure_file(self):
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        s_file = self.workspace_dir / "schedules.json"
        if not s_file.exists():
            with open(s_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def list_schedules(self) -> list[dict[str, Any]]:
        s_file = self.workspace_dir / "schedules.json"
        try:
            with open(s_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def add_schedule(self, schedule_data: dict[str, Any]) -> dict[str, Any]:
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
            "created_at": datetime.now(UTC).isoformat(),
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

        # Register persistent OS-level Windows Task if on win32
        if sys.platform == "win32" and hour >= 0:
            try:
                self.register_windows_task(
                    task_id=task_id,
                    hour=hour,
                    minute=minute,
                    prompt=entry.get("prompt", "")
                )
            except Exception as e:
                logger.debug(f"Windows Task Scheduler registration note: {e}")

        return entry

    @classmethod
    def register_windows_task(
        cls,
        task_id: str,
        hour: int,
        minute: int,
        prompt: str,
        python_exe: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Creates a persistent OS-level Windows Task using schtasks.exe.
        Ensures the scheduled mission executes automatically at the designated time
        even if the interactive terminal is closed.
        """
        if sys.platform != "win32":
            return {"success": False, "error": "Windows Task Scheduler is only supported on win32."}

        if hour < 0:
            return {"success": True, "task_name": "In-Memory Daemon Loop", "platform": "asyncio"}

        py_bin = python_exe or sys.executable
        cli_path = Path(__file__).resolve().parent.parent / "jarvis_cli.py"
        safe_prompt = prompt.replace('"', '\\"')
        task_name = f"JARVIS_{task_id}"
        time_str = f"{hour:02d}:{minute:02d}"

        cmd_run = f'"{py_bin}" "{cli_path}" "{safe_prompt}"'
        schtasks_cmd = f'schtasks /Create /SC DAILY /TN "{task_name}" /TR "{cmd_run}" /ST {time_str} /F'

        try:
            res = subprocess.run(schtasks_cmd, shell=True, capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                return {"success": True, "task_name": task_name, "scheduled_time": time_str, "output": res.stdout.strip()}
            else:
                return {"success": False, "task_name": task_name, "error": res.stderr.strip() or res.stdout.strip()}
        except Exception as e:
            return {"success": False, "task_name": task_name, "error": str(e)}

    @classmethod
    def delete_windows_task(cls, task_id: str) -> dict[str, Any]:
        """Deletes a registered Windows Task."""
        if sys.platform != "win32":
            return {"success": False}
        task_name = f"JARVIS_{task_id}"
        try:
            res = subprocess.run(f'schtasks /Delete /TN "{task_name}" /F', shell=True, capture_output=True, text=True, timeout=10)
            return {"success": res.returncode == 0}
        except Exception:
            return {"success": False}

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
            if sys.platform == "win32":
                try:
                    self.delete_windows_task(task_id)
                except Exception:
                    pass
            return True
        return False

    def update_schedule_run_status(self, task_id: str, run_date_str: str):
        schedules = self.list_schedules()
        now = datetime.now()
        for s in schedules:
            if s.get("task_id") == task_id or s.get("id") == task_id:
                s["last_run_at"] = datetime.now(UTC).isoformat()
                s["last_run_date"] = run_date_str
                s["last_run_hour"] = now.strftime("%Y-%m-%d %H")
                s["last_run_ts"] = now.timestamp()
                s["run_count"] = int(s.get("run_count", 0)) + 1
                self._save_schedules(schedules)
                break

    def _save_schedules(self, schedules: list[dict[str, Any]]):
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
                current_hour_str = now.strftime("%Y-%m-%d %H")
                now_ts = now.timestamp()

                schedules = self.list_schedules()
                for sched in schedules:
                    if not sched.get("is_active", True):
                        continue
                    s_hour = int(sched.get("hour", 6))
                    s_minute = int(sched.get("minute", 0))
                    tid = sched.get("task_id") or sched.get("id") or "sched"
                    last_run_ts = sched.get("last_run_ts") or 0.0

                    should_trigger = False
                    status_marker = today_str

                    if s_hour == -1 and s_minute == -1:
                        # 1. Continuous 24/7 Daemon Loop: Triggers every cadence cycle (minimum 60s cooldown)
                        if now_ts - last_run_ts >= 60:
                            should_trigger = True
                            status_marker = today_str
                    elif s_hour == -1 and s_minute >= 0:
                        # 2. Hourly Mission: Triggers at designated minute of every hour
                        if current_minute == s_minute and sched.get("last_run_hour") != current_hour_str:
                            should_trigger = True
                            status_marker = current_hour_str
                    else:
                        # 3. Daily Scheduled Mission: Triggers at designated hour & minute once per day
                        if current_hour == s_hour and current_minute == s_minute and sched.get("last_run_date") != today_str:
                            should_trigger = True
                            status_marker = today_str

                    if should_trigger:
                        print(f"[Scheduler] ⏰ Triggering scheduled mission '{sched.get('title')}' at {now.strftime('%H:%M:%S')}...")
                        self.update_schedule_run_status(tid, status_marker)
                        prompt_to_run = sched.get("prompt", "")
                        
                        if hasattr(orchestrator_instance, "process_directive"):
                            asyncio.create_task(orchestrator_instance.process_directive(prompt_to_run))
                        elif hasattr(orchestrator_instance, "run_scheduled_mission"):
                            asyncio.create_task(
                                orchestrator_instance.run_scheduled_mission(
                                    prompt=prompt_to_run,
                                    title=sched.get("title", "Daily Autonomous Mission")
                                )
                            )
                        else:
                            try:
                                from jarvis_cli import JarvisCLI
                                cli = JarvisCLI()
                                asyncio.create_task(cli.process_directive(prompt_to_run))
                            except Exception as e:
                                print(f"[Scheduler Execution Error] {e}")
            except Exception as e:
                print(f"[Scheduler Loop Error] {e}")
            await asyncio.sleep(poll_interval_sec)

# Global Singleton Scheduler
scheduler = AutonomousScheduler()

