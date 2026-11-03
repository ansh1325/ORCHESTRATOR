"""
JARVIS Ambient Visual Streaming Engine
Chief Systems Architect: Ansh Tiwari

Continuous Optical Presence:
1. Low-Overhead Screen Stream: Continuously samples desktop frame thumbnails (e.g. 1 FPS) in a background thread.
2. Visual Frame Diffing: Computes difference metrics between consecutive frames to detect sudden changes (errors, popups, build completions).
3. Rolling Visual Memory: Maintains a timeline of the last 15 visual events and screen state hashes in workspaces/screenshots/ambient_history.
4. Instant Context Retrieval: Allows JARVIS to instantly know what Master Ansh is looking at without waiting for an on-demand capture.
"""

import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

from PIL import Image

from core.config import settings
from core.os_operator import OSOperator

logger = logging.getLogger("Jarvis.AmbientVision")


class AmbientVisionEngine:
    """Continuous Background Optical Stream & Visual Change Detector."""

    AMBIENT_DIR: Path = settings.WORKSPACE_DIR / "screenshots" / "ambient_history"

    def __init__(self, sample_interval_seconds: float = 2.0, change_threshold: float = 0.05):
        self.interval = sample_interval_seconds
        self.change_threshold = change_threshold
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_frame_hash: str = ""
        self._last_thumbnail: Image.Image | None = None
        self.visual_event_history: list[dict[str, Any]] = []
        self._ensure_dir()

    def _ensure_dir(self):
        self.AMBIENT_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def compute_frame_hash(cls, img: Image.Image) -> str:
        """Computes perceptual MD5 hash of 160x90 downsampled grayscale image."""
        try:
            thumb = img.convert("L").resize((160, 90), Image.Resampling.BILINEAR)
            raw_bytes = thumb.tobytes()
            return hashlib.md5(raw_bytes).hexdigest()
        except Exception:
            return ""

    @classmethod
    def calculate_frame_difference(cls, prev_img: Image.Image | None, curr_img: Image.Image) -> float:
        """
        Calculates normalized pixel difference (0.0 to 1.0) between consecutive frames.
        """
        if prev_img is None:
            return 1.0
        try:
            prev_small = prev_img.convert("L").resize((160, 90), Image.Resampling.BILINEAR)
            curr_small = curr_img.convert("L").resize((160, 90), Image.Resampling.BILINEAR)
            diffs = 0
            p1 = prev_small.tobytes()
            p2 = curr_small.tobytes()
            total_pixels = len(p1)
            for v1, v2 in zip(p1, p2):
                if abs(v1 - v2) > 20:
                    diffs += 1
            return diffs / total_pixels if total_pixels > 0 else 0.0
        except Exception as e:
            logger.debug(f"Frame difference calculation exception: {e}")
            return 0.0

    def capture_ambient_frame(self) -> dict[str, Any]:
        """Captures a single frame, calculates diff, and records significant visual shifts."""
        timestamp = time.time()
        screenshot_path = OSOperator.capture_desktop_screen("ambient_latest.png")
        diff_ratio = 0.0
        is_significant_change = False

        try:
            curr_img = Image.open(screenshot_path)
            curr_hash = self.compute_frame_hash(curr_img)
            diff_ratio = self.calculate_frame_difference(self._last_thumbnail, curr_img)

            if diff_ratio >= self.change_threshold or not self._last_frame_hash:
                is_significant_change = True
                event_id = f"vis_{int(timestamp * 1000)}"
                event_path = self.AMBIENT_DIR / f"{event_id}.png"
                curr_img.save(event_path)

                event = {
                    "id": event_id,
                    "timestamp": timestamp,
                    "diff_ratio": round(diff_ratio, 4),
                    "frame_hash": curr_hash,
                    "image_path": str(event_path),
                    "resolution": curr_img.size
                }
                self.visual_event_history.append(event)
                # Keep rolling history limited to last 20 events
                self.visual_event_history = self.visual_event_history[-20:]
                logger.info(f"Visual change detected ({round(diff_ratio*100, 1)}% diff): {event_id}")

            self._last_thumbnail = curr_img
            self._last_frame_hash = curr_hash

        except Exception as e:
            logger.debug(f"Ambient frame capture error: {e}")

        return {
            "timestamp": timestamp,
            "diff_ratio": round(diff_ratio, 4),
            "changed": is_significant_change,
            "current_hash": self._last_frame_hash
        }

    def start_streaming(self) -> bool:
        """Starts background ambient screen sampling thread."""
        if self._running:
            return True
        self._running = True

        def _loop():
            logger.info("Ambient Visual Streaming Engine online (1 FPS).")
            while self._running:
                try:
                    self.capture_ambient_frame()
                except Exception as e:
                    logger.debug(f"Ambient stream error: {e}")
                time.sleep(self.interval)

        self._thread = threading.Thread(target=_loop, daemon=True, name="JarvisAmbientVisionThread")
        self._thread.start()
        return True

    def stop_streaming(self) -> bool:
        """Stops background visual streaming."""
        self._running = False
        logger.info("Ambient Visual Streaming Engine offline.")
        return True

    def get_recent_visual_context(self) -> list[dict[str, Any]]:
        """Returns the recent timeline of visual changes."""
        return self.visual_event_history[-10:]

    def get_status(self) -> dict[str, Any]:
        return {
            "active": self._running,
            "sample_interval": self.interval,
            "change_threshold": self.change_threshold,
            "total_events_captured": len(self.visual_event_history),
            "recent_events": self.visual_event_history[-3:]
        }


ambient_vision_engine = AmbientVisionEngine()
