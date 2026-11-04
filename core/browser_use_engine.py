"""
Browser-Use Autonomous Agent Engine Module
Creator: Ansh Tiwari (Chief Systems Architect)

Integrates the official 'browser-use' framework (github.com/browser-use/browser-use)
into JARVIS's cognitive multi-agent operating system:
1. Set-of-Marks visual perception with multi-step vision-action loops.
2. Full integration with Groq LPUs (Meta Llama 3.3 70B / 3.1 70B) and OpenAI endpoints.
3. Persistent session bridge into '~/.llama_orchestrator/browser_profile'
   (so user stays logged into Google, LeetCode, GitHub, LinkedIn across all sessions).
4. Direct autonomous objective execution with closed-loop verification.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

from core.browser_controller import BrowserController
from core.config import settings

logger = logging.getLogger("BrowserUseEngine")


class BrowserUseEngine:
    """
    Autonomous Vision-Action Web Agent powered by 'browser-use'.
    Enables JARVIS to dynamically explore, interact with, and solve tasks on any website
    without brittle hardcoded DOM selectors.
    """

    def __init__(self):
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Checks if browser-use is installed and importable."""
        if self._available is not None:
            return self._available
        try:
            import browser_use  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False
        return self._available

    def get_llm(self) -> Any:
        """
        Dynamically configures the optimal LLM for browser-use.
        Prioritizes Groq (Meta Llama 3.3 70B) for ultra-fast inference,
        falling back to OpenAI if configured.
        """
        try:
            from browser_use.llm import ChatGroq, ChatOpenAI
        except ImportError as e:
            raise RuntimeError(f"browser-use LLM imports failed: {e}")

        # 1. Groq Multimodal Meta Vision Provider (Llama 3.2 11B / 90B Vision)
        groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
        if groq_key and not groq_key.startswith("your_"):
            # Primary: Meta Llama 3.2 Vision for Set-of-Marks pixel grounding
            vision_model = os.getenv("META_VISION_MODEL", "llama-3.2-11b-vision-preview")
            try:
                return ChatGroq(
                    model=vision_model,
                    api_key=groq_key,
                    temperature=0.2,
                    max_retries=3
                )
            except Exception:
                return ChatGroq(
                    model="llama-3.3-70b-versatile",
                    api_key=groq_key,
                    temperature=0.2,
                    max_retries=3
                )

        # 2. OpenAI Provider
        openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if openai_key and not openai_key.startswith("your_"):
            return ChatOpenAI(
                model="gpt-4o",
                api_key=openai_key,
                temperature=0.2
            )

        # Fallback to local or default mock
        return None

    def get_browser_profile(self, headless: bool = False) -> Any:
        """
        Creates a BrowserProfile sharing JARVIS's persistent profile directory
        and discovered host browser executable.
        """
        from browser_use import BrowserProfile

        user_data_dir = str(Path.home() / ".llama_orchestrator" / "browser_profile")
        os.makedirs(user_data_dir, exist_ok=True)

        exec_path = BrowserController.get_system_default_browser_executable()

        profile_kwargs: dict[str, Any] = {
            "headless": headless,
            "user_data_dir": user_data_dir,
            "keep_alive": True,
            "disable_security": False,
        }

        if exec_path and Path(exec_path).exists():
            profile_kwargs["executable_path"] = exec_path

        return BrowserProfile(**profile_kwargs)

    async def execute_task(
        self,
        task: str,
        max_steps: int = 15,
        headless: bool = False
    ) -> dict[str, Any]:
        """
        Executes a high-level autonomous browser task using browser-use Agent.
        Returns execution results, history, and status.
        """
        if not self.is_available():
            return {
                "success": False,
                "task": task,
                "error": "browser-use package is not available in the current environment.",
            }

        from browser_use import Agent

        llm = self.get_llm()
        if llm is None:
            return {
                "success": False,
                "task": task,
                "error": "No valid API key (GROQ_API_KEY or OPENAI_API_KEY) found to power browser-use LLM.",
            }

        profile = self.get_browser_profile(headless=headless)

        logger.info(f"[BrowserUseEngine] Initializing agent for task: '{task}'")
        try:
            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=profile,
                use_vision=True,
                max_actions_per_step=4,
            )

            history = await agent.run(max_steps=max_steps)
            final_result = history.final_result() if hasattr(history, "final_result") else str(history)

            return {
                "success": True,
                "task": task,
                "result": final_result,
                "steps_taken": len(history.history) if hasattr(history, "history") else 0,
                "history": str(history)
            }
        except Exception as e:
            logger.error(f"[BrowserUseEngine] Execution error: {e}", exc_info=True)
            return {
                "success": False,
                "task": task,
                "error": str(e)
            }

    def execute_task_sync(
        self,
        task: str,
        max_steps: int = 15,
        headless: bool = False
    ) -> dict[str, Any]:
        """Synchronous wrapper for execute_task."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    lambda: asyncio.run(self.execute_task(task, max_steps=max_steps, headless=headless))
                )
                return future.result()
        else:
            return asyncio.run(self.execute_task(task, max_steps=max_steps, headless=headless))


# Singleton instance
browser_use_engine = BrowserUseEngine()

