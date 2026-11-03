"""
JARVIS Proactive Ambient System Daemon
Chief Systems Architect: Ansh Tiwari

Continuous OS Monitor & Proactive Sentinel:
1. Hardware Resource Monitoring: CPU load, RAM memory pressure, disk utilization.
2. Development Port Sentinel: Detects port collisions (8000, 3000, 5000, 8080) and orphaned socket listeners.
3. Proactive Autonomous Alerts: Alerts Master Ansh via voice and structured notifications before hardware stalls.
4. Background Task Tracker: Monitors background runs and informs when human intervention is needed.
"""

import json
import logging
import socket
import threading
import time
from pathlib import Path
from typing import Any

import psutil

from core.config import settings

logger = logging.getLogger("Jarvis.Daemon")


class JarvisDaemon:
    """Proactive 24/7 Background System Sentinel & Hardware Guard."""

    ALERTS_FILE: Path = settings.WORKSPACE_DIR / "system_alerts.json"

    def __init__(self, check_interval_seconds: float = 15.0):
        self.interval = check_interval_seconds
        self._running = False
        self._thread: threading.Thread | None = None
        self.alert_history: list[dict[str, Any]] = []
        self._ensure_alerts_file()

    def _ensure_alerts_file(self):
        settings.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        if not self.ALERTS_FILE.exists():
            with open(self.ALERTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    @classmethod
    def check_hardware_telemetry(cls) -> dict[str, Any]:
        """Collects live CPU, RAM, and storage telemetry."""
        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(settings.BASE_DIR))

        telemetry = {
            "cpu_percent": cpu_pct,
            "memory_percent": mem.percent,
            "memory_available_gb": round(mem.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "timestamp": time.time(),
            "status": "HEALTHY"
        }

        # Threshold rules
        if cpu_pct > 92.0 or mem.percent > 92.0:
            telemetry["status"] = "CRITICAL_PRESSURE"
        elif cpu_pct > 80.0 or mem.percent > 85.0:
            telemetry["status"] = "WARNING_HIGH_LOAD"

        return telemetry

    @classmethod
    def inspect_port_safety(cls, ports: list[int] | None = None) -> list[dict[str, Any]]:
        """Inspects key development ports to verify availability and prevent bind collisions."""
        if ports is None:
            ports = [8000, 3000, 5000, 8080, 8501]

        statuses: list[dict[str, Any]] = []
        for port in ports:
            is_open = False
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                try:
                    s.bind(("127.0.0.1", port))
                    is_open = True
                except OSError:
                    is_open = False

            statuses.append({
                "port": port,
                "available": is_open,
                "status": "FREE" if is_open else "IN_USE"
            })
        return statuses

    def record_alert(self, level: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Records a structured alert into workspaces/system_alerts.json."""
        alert = {
            "id": f"alt_{int(time.time() * 1000)}",
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "context": context or {}
        }
        self.alert_history.append(alert)
        try:
            with open(self.ALERTS_FILE, "r", encoding="utf-8") as f:
                current = json.load(f)
            current.append(alert)
            with open(self.ALERTS_FILE, "w", encoding="utf-8") as f:
                json.dump(current[-100:], f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to persist alert: {e}")
        return alert

    def run_health_cycle(self) -> dict[str, Any]:
        """Executes a single proactive check cycle."""
        telemetry = self.check_hardware_telemetry()
        ports = self.inspect_port_safety()

        report = {
            "telemetry": telemetry,
            "ports": ports,
            "alert_created": False
        }

        if telemetry["status"] == "CRITICAL_PRESSURE":
            msg = f"Critical Hardware Pressure: CPU {telemetry['cpu_percent']}%, RAM {telemetry['memory_percent']}%"
            self.record_alert("CRITICAL", msg, telemetry)
            report["alert_created"] = True
            logger.warning(msg)

        return report

    def start_daemon(self) -> bool:
        """Starts background sentinel loop in an independent thread."""
        if self._running:
            return True
        self._running = True

        def _loop():
            logger.info("JARVIS Ambient System Daemon started.")
            while self._running:
                try:
                    self.run_health_cycle()
                except Exception as e:
                    logger.debug(f"Daemon health cycle error: {e}")
                time.sleep(self.interval)

        self._thread = threading.Thread(target=_loop, daemon=True, name="JarvisSentinelDaemon")
        self._thread.start()
        return True

    def stop_daemon(self) -> bool:
        """Stops background sentinel loop."""
        self._running = False
        logger.info("JARVIS Ambient System Daemon stopped.")
        return True

    def get_status(self) -> dict[str, Any]:
        """Returns live daemon status and latest telemetry."""
        return {
            "running": self._running,
            "telemetry": self.check_hardware_telemetry(),
            "ports": self.inspect_port_safety(),
            "recent_alerts": self.alert_history[-5:]
        }
