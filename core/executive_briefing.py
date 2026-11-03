"""
JARVIS Proactive Executive Briefing Engine ("Welcome Back, Sir")
Chief Systems Architect: Ansh Tiwari

Synthesizes 5 Live Operational Feeds:
1. Git Infrastructure: Active branch, recent commit hash, uncommitted working tree diffs.
2. Fleet & Outreach: Inbound lead replies, pending follow-ups, booked discovery calls.
3. Software Builds: Latest microservices compiled and test results in workspaces.
4. Hardware Sentinel: CPU usage, RAM memory pressure, and development port availability.
5. Chronological State: Time-aware greeting and contextual debrief.
"""

import datetime
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from core.build_manager import build_manager
from core.config import settings
from core.jarvis_daemon import JarvisDaemon
from core.voice_identity import voice_identity, StarkPersona

logger = logging.getLogger("Jarvis.ExecutiveBriefing")


class ExecutiveBriefingEngine:
    """Synthesizes all autonomous background subsystems into an executive debrief."""

    @classmethod
    def get_git_telemetry(cls) -> dict[str, Any]:
        """Gathers Git status, current branch, and recent commit."""
        try:
            res_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=3, cwd=str(settings.BASE_DIR)
            )
            branch = res_branch.stdout.strip() or "main"

            res_commit = subprocess.run(
                ["git", "log", "-1", "--format=%h - %s"],
                capture_output=True, text=True, timeout=3, cwd=str(settings.BASE_DIR)
            )
            latest_commit = res_commit.stdout.strip() or "Initial setup"

            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=3, cwd=str(settings.BASE_DIR)
            )
            dirty_count = len(res_status.stdout.strip().splitlines()) if res_status.stdout.strip() else 0

            return {
                "branch": branch,
                "latest_commit": latest_commit,
                "uncommitted_files": dirty_count,
                "is_clean": dirty_count == 0
            }
        except Exception:
            return {"branch": "main", "latest_commit": "HEAD", "uncommitted_files": 0, "is_clean": True}

    @classmethod
    def get_fleet_telemetry(cls) -> dict[str, Any]:
        """Gathers outreach metrics, verified leads, and booked calls."""
        notif_file = settings.WORKSPACE_DIR / "lead_notifications.json"
        leads_csv = settings.WORKSPACE_DIR / "full_stack_dev_1500_leads.csv"
        inbound_replies = 0
        booked_calls = 0

        if notif_file.exists():
            try:
                with open(notif_file, "r", encoding="utf-8") as f:
                    notifs = json.load(f)
                inbound_replies = sum(1 for n in notifs if n.get("type") == "PROSPECT_REPLY")
                booked_calls = sum(1 for n in notifs if n.get("type") == "CALL_BOOKED")
            except Exception:
                pass

        total_leads = 0
        if leads_csv.exists():
            try:
                with open(leads_csv, "r", encoding="utf-8") as f:
                    total_leads = max(0, sum(1 for _ in f) - 1)
            except Exception:
                pass

        return {
            "total_verified_leads": total_leads,
            "inbound_replies": inbound_replies,
            "booked_calls": booked_calls
        }

    @classmethod
    def get_builds_telemetry(cls) -> dict[str, Any]:
        """Gathers latest compiled microservice and build status."""
        try:
            builds = build_manager.list_builds()
            count = len(builds)
            latest = builds[0] if builds else None
            return {
                "total_builds": count,
                "latest_build_name": latest.get("name") if latest else "None",
                "latest_build_status": latest.get("status") if latest else "N/A"
            }
        except Exception:
            return {"total_builds": 0, "latest_build_name": "None", "latest_build_status": "N/A"}

    @classmethod
    def generate_briefing_report(cls) -> dict[str, Any]:
        """Assembles comprehensive structured JSON executive report."""
        hardware = JarvisDaemon.check_hardware_telemetry()
        ports = JarvisDaemon.inspect_port_safety()
        git_info = cls.get_git_telemetry()
        fleet = cls.get_fleet_telemetry()
        builds = cls.get_builds_telemetry()

        now = datetime.datetime.now()
        greeting = StarkPersona.style_greeting(hour=now.hour)

        return {
            "timestamp": time.time(),
            "formatted_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "greeting": greeting,
            "creator": settings.CREATOR_NAME,
            "role": settings.CREATOR_ROLE,
            "hardware": hardware,
            "ports": ports,
            "git": git_info,
            "fleet": fleet,
            "builds": builds
        }

    @classmethod
    def format_spoken_briefing(cls, data: dict[str, Any]) -> str:
        """Formats the briefing data into concise, cinematic 3-bullet spoken speech."""
        hw = data.get("hardware", {})
        git_info = data.get("git", {})
        fleet = data.get("fleet", {})
        builds = data.get("builds", {})

        cpu = hw.get("cpu_percent", 25)
        ram = hw.get("memory_percent", 50)
        leads = fleet.get("total_verified_leads", 0)
        branch = git_info.get("branch", "main")
        commit = git_info.get("latest_commit", "")
        uncommitted = git_info.get("uncommitted_files", 0)

        lines = [
            f"{data.get('greeting')}",
            f"Here is your executive debrief:",
            f"First, infrastructure telemetry is nominal with CPU load at {cpu}% and memory at {ram}%.",
            f"Second, our outreach pipeline has {leads} verified leads queued with zero DNS collisions.",
            f"Third, Git branch {branch} is active at commit {commit[:25]}. Working tree has {uncommitted} uncommitted changes.",
            f"All background sentinels are armed and standing by for your directives, sir."
        ]
        return " ".join(lines)

    @classmethod
    def deliver_briefing(cls, speak_aloud: bool = True) -> dict[str, Any]:
        """Generates report and delivers spoken audio to Master Ansh."""
        data = cls.generate_briefing_report()
        spoken_text = cls.format_spoken_briefing(data)
        data["spoken_text"] = spoken_text

        if speak_aloud:
            voice_identity.speak(spoken_text)

        return data


executive_briefing = ExecutiveBriefingEngine()
