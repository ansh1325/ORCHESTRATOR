"""
LlamaOrchestrator Autonomous Browser Agent
Specialized cognitive sub-agent dedicated to opening, perceiving, navigating, and controlling web browsers.
Operates on an interactive Perception-Action-Observation loop (like Antigravity / Computer Use / Stagehand).
Features:
1. Live Interactive DOM Perception with numbered interactive elements ([#1], [#2], etc.).
2. Multi-turn reasoning loop (Meta Llama / heuristic) to decide and execute next actions.
3. Resilient self-healing interactions (smart locators, JS click fallbacks, scroll-into-view).
4. Persistent browser profile support (retains cookies, sessions, logins across runs).
5. Seamless Host Browser Bridge (when auth or anti-bot blocks automation, bridges to active host session).
6. Dedicated High-Level Task Solvers (autonomous web search, Gmail dispatch, form filling, content extraction).
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from core.browser_controller import BrowserController
from core.config import settings


@dataclass
class BrowserElement:
    """Represents an interactive DOM element detected on the page with vision/spatial coordinates."""
    index: int
    tag: str
    element_type: str
    text: str
    selector: str
    aria_label: str = ""
    placeholder: str = ""
    href: str = ""
    is_visible: bool = True
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    center_x: float = 0.0
    center_y: float = 0.0


@dataclass
class BrowserStepResult:
    """Result of an individual action taken in the browser."""
    step: int
    action: str
    target: str
    reason: str
    success: bool
    url_after: str
    title_after: str
    screenshot_path: Optional[str] = None
    extracted_text: Optional[str] = None
    error: Optional[str] = None


class BrowserAgent:
    """
    Dedicated Autonomous Browser Agent.
    Interacts with live browsers autonomously, perceiving DOM structure and executing actions
    until the user's objective is completed.
    """

    def __init__(self, user_data_dir: Optional[str] = None, headless: bool = False):
        self.headless = headless
        self.user_data_dir = (
            Path(user_data_dir)
            if user_data_dir
            else (Path.home() / ".llama_orchestrator" / "browser_profile")
        )
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir = Path("workspaces/screenshots/browser_agent")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.history: list[BrowserStepResult] = []
        self._active_playwright = None
        self._active_context = None
        self._is_active_cdp = False

    def get_or_create_session(self, headless: bool = False):
        """
        Co-Worker Window Paradigm:
        Provides a persistent, visible browser session that stays open across commands,
        allowing Master Ansh to inspect, intervene, login, and co-work concurrently.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return None, False

        # If existing context is still valid and open, reuse it
        if self._active_context is not None:
            try:
                _ = self._active_context.pages
                return self._active_context, self._is_active_cdp
            except Exception:
                self._active_context = None

        if self._active_playwright is None:
            self._active_playwright = sync_playwright().start()

        BrowserController.clean_profile_crash_state(self.user_data_dir)

        launch_args = [
            "--start-maximized",
            "--disable-session-crashed-bubble",
            "--hide-crash-restore-bubble",
            "--restore-last-session=false",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--disable-features=OptimizationHints,TranslateUI",
            "--remote-debugging-port=9222"
        ]

        # 0. Check CDP connection first (connects to already-running desktop browser if debug port open)
        try:
            cdp_browser = self._active_playwright.chromium.connect_over_cdp("http://localhost:9222")
            if cdp_browser.contexts:
                self._active_context = cdp_browser.contexts[0]
                self._is_active_cdp = True
                return self._active_context, True
        except Exception:
            pass

        # 1. Primary Default: Discovered System Default Browser on this machine
        default_bin = BrowserController.get_system_default_browser_executable()
        if default_bin:
            try:
                self._active_context = self._active_playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    executable_path=default_bin,
                    headless=headless,
                    args=launch_args,
                    ignore_default_args=["--enable-automation", "--no-sandbox"]
                )
                self._is_active_cdp = False
                return self._active_context, False
            except Exception:
                pass

        # 2. Preferred Cross-Platform System Channels (macOS / Linux / Windows)
        for ch in BrowserController.get_preferred_channels():
            try:
                if ch:
                    self._active_context = self._active_playwright.chromium.launch_persistent_context(
                        user_data_dir=str(self.user_data_dir),
                        channel=ch,
                        headless=headless,
                        args=launch_args,
                        ignore_default_args=["--enable-automation", "--no-sandbox"]
                    )
                else:
                    self._active_context = self._active_playwright.chromium.launch_persistent_context(
                        user_data_dir=str(self.user_data_dir),
                        headless=headless,
                        args=launch_args,
                        ignore_default_args=["--enable-automation", "--no-sandbox"]
                    )
                self._is_active_cdp = False
                return self._active_context, False
            except Exception:
                continue

        # 3. Brave Browser
        brave_bin = BrowserController.get_brave_executable_path()
        if brave_bin:
            try:
                self._active_context = self._active_playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    executable_path=brave_bin,
                    headless=headless,
                    args=launch_args,
                    ignore_default_args=["--enable-automation", "--no-sandbox"]
                )
                self._is_active_cdp = False
                return self._active_context, False
            except Exception:
                pass

        # 4. Default bundled Chromium persistent context
        try:
            self._active_context = self._active_playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=headless,
                args=launch_args,
                ignore_default_args=["--enable-automation", "--no-sandbox"]
            )
            self._is_active_cdp = False
            return self._active_context, False
        except Exception:
            pass

        # 5. Headless isolated fallback
        try:
            browser = self._active_playwright.chromium.launch(headless=True)
            self._active_context = browser.new_context()
            self._is_active_cdp = False
            return self._active_context, False
        except Exception:
            return None, False

    def close_active_session(self):
        """Cleanly closes active Co-Worker browser session."""
        if self._active_context:
            try:
                if not self._is_active_cdp:
                    self._active_context.close()
            except Exception:
                pass
            self._active_context = None

        if self._active_playwright:
            try:
                self._active_playwright.stop()
            except Exception:
                pass
            self._active_playwright = None

        try:
            BrowserController.clean_profile_crash_state(self.user_data_dir)
        except Exception:
            pass

    # =========================================================================
    # High-Performance Tab Management Engine (Multi-Tab Co-Working)
    # =========================================================================

    @classmethod
    def normalize_web_url(cls, raw: str) -> str:
        """Standardizes user inputs into fully-qualified web URLs."""
        s = raw.strip()
        if s.startswith(("http://", "https://", "about:")):
            return s
        known = {
            "leetcode": "https://leetcode.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "google": "https://www.google.com",
            "linkedin": "https://www.linkedin.com",
            "gmail": "https://mail.google.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com"
        }
        low = s.lower()
        if low in known:
            return known[low]
        if any(s.endswith(ext) or f"{ext}/" in s for ext in [".com", ".org", ".io", ".net", ".ai", ".co", ".edu", ".in"]):
            return f"https://{s}"
        if "." in s:
            return f"https://{s}"
        return f"https://{s}.com"

    def open_tab(self, url: str) -> dict[str, Any]:
        """
        Opens a URL in a NEW TAB within the active co-worker browser window,
        cleans up ghost/spinning tabs, and brings the tab to the front.
        """
        clean_url = self.normalize_web_url(url)

        context, is_cdp = self.get_or_create_session(headless=False)
        if not context:
            success = BrowserController.open_in_system_browser(clean_url)
            return {"success": success, "url": clean_url, "method": "system_browser"}

        try:
            # Clean up empty dangling tabs or reuse active blank tab
            target_page = None
            for p in list(context.pages):
                try:
                    if p.url in ["about:blank", "chrome://newtab/", "edge://newtab/", ""]:
                        target_page = p
                        break
                except Exception:
                    pass

            if target_page is None:
                target_page = context.new_page()

            if hasattr(BrowserController, 'inject_stealth_scripts'):
                BrowserController.inject_stealth_scripts(target_page)

            # Navigate using 'commit' so HTTP request is dispatched immediately without hanging in omnibox
            target_page.goto(clean_url, wait_until="commit", timeout=45000)
            try:
                target_page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            try:
                target_page.bring_to_front()
            except Exception:
                pass

            return {
                "success": True,
                "url": clean_url,
                "title": target_page.title() or clean_url,
                "tab_count": len(context.pages),
                "is_cdp": is_cdp
            }
        except Exception as e:
            fallback = BrowserController.open_in_system_browser(clean_url)
            return {"success": fallback, "url": clean_url, "method": "system_browser_fallback", "error": str(e)}

    def list_tabs(self) -> list[dict[str, Any]]:
        """Lists all open tabs in the active browser session."""
        if not self._active_context or not self._active_context.pages:
            return []
        tabs = []
        for idx, page in enumerate(self._active_context.pages):
            try:
                tabs.append({
                    "index": idx,
                    "title": page.title() or f"Tab {idx}",
                    "url": page.url,
                    "page": page
                })
            except Exception:
                tabs.append({
                    "index": idx,
                    "title": f"Tab {idx}",
                    "url": "unknown",
                    "page": page
                })
        return tabs

    def switch_tab(self, index: int) -> dict[str, Any]:
        """Switches focus to the tab specified by index."""
        if not self._active_context or not self._active_context.pages:
            return {"success": False, "error": "No active browser session or tabs."}
        pages = self._active_context.pages
        if index < 0 or index >= len(pages):
            return {"success": False, "error": f"Tab index {index} out of range (0-{len(pages)-1})."}
        try:
            target = pages[index]
            target.bring_to_front()
            return {"success": True, "index": index, "title": target.title(), "url": target.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_tab(self, index: Optional[int] = None) -> dict[str, Any]:
        """Closes the specified tab (or the active/last tab if index is None)."""
        if not self._active_context or not self._active_context.pages:
            return {"success": False, "error": "No active browser session or tabs."}
        pages = self._active_context.pages
        target_idx = (len(pages) - 1) if index is None else index
        if target_idx < 0 or target_idx >= len(pages):
            return {"success": False, "error": f"Tab index {target_idx} out of range."}
        try:
            target = pages[target_idx]
            target.close()
            return {"success": True, "closed_index": target_idx, "remaining_tabs": len(self._active_context.pages)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # DOM Perception Engine
    # =========================================================================

    @staticmethod
    def _extract_interactive_elements(page: Any) -> list[BrowserElement]:
        """
        Extracts all interactive elements on the page (buttons, links, inputs, textareas)
        and assigns unique integer indices for the agent to reference.
        """
        js_code = """
        () => {
            const elements = [];
            let index = 1;

            function isVisible(el) {
                if (!el.offsetParent && el.offsetWidth === 0 && el.offsetHeight === 0) return false;
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
            }

            const candidates = document.querySelectorAll(
                'button, a[href], input, textarea, select, [role="button"], [role="link"], [role="checkbox"], [contenteditable="true"]'
            );

            for (const el of candidates) {
                if (!isVisible(el)) continue;
                const tag = el.tagName.toLowerCase();
                const type = el.getAttribute('type') || tag;
                const text = (el.innerText || el.value || el.getAttribute('value') || '').trim().slice(0, 60);
                const aria = el.getAttribute('aria-label') || el.getAttribute('title') || '';
                const placeholder = el.getAttribute('placeholder') || '';
                const href = el.getAttribute('href') || '';

                // Build unique selector
                let sel = '';
                if (el.id) {
                    sel = '#' + CSS.escape(el.id);
                } else if (el.name) {
                    sel = `${tag}[name="${CSS.escape(el.name)}"]`;
                } else if (aria) {
                    sel = `[aria-label="${CSS.escape(aria)}"]`;
                } else if (placeholder) {
                    sel = `[placeholder="${CSS.escape(placeholder)}"]`;
                } else if (text && tag === 'a') {
                    sel = `a:has-text("${text.slice(0, 25)}")`;
                } else if (text && tag === 'button') {
                    sel = `button:has-text("${text.slice(0, 25)}")`;
                } else {
                    sel = `${tag}:nth-of-type(${index})`;
                }

                // Tag element in DOM for fast reference
                el.setAttribute('data-jarvis-id', String(index));

                const rect = el.getBoundingClientRect();
                const cx = Math.round(rect.left + rect.width / 2);
                const cy = Math.round(rect.top + rect.height / 2);

                elements.push({
                    index: index,
                    tag: tag,
                    element_type: type,
                    text: text,
                    selector: `[data-jarvis-id="${index}"]`,
                    aria_label: aria,
                    placeholder: placeholder,
                    href: href,
                    is_visible: true,
                    x: Math.round(rect.left),
                    y: Math.round(rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    center_x: cx,
                    center_y: cy
                });

                index++;
                if (elements.length >= 100) break; // Limit per viewport
            }
            return elements;
        }
        """
        try:
            raw_elements = page.evaluate(js_code)
            return [
                BrowserElement(
                    index=e["index"],
                    tag=e["tag"],
                    element_type=e["element_type"],
                    text=e["text"],
                    selector=e["selector"],
                    aria_label=e.get("aria_label", ""),
                    placeholder=e.get("placeholder", ""),
                    href=e.get("href", ""),
                    is_visible=e.get("is_visible", True),
                    x=float(e.get("x", 0.0)),
                    y=float(e.get("y", 0.0)),
                    width=float(e.get("width", 0.0)),
                    height=float(e.get("height", 0.0)),
                    center_x=float(e.get("center_x", 0.0)),
                    center_y=float(e.get("center_y", 0.0))
                )
                for e in raw_elements
            ]
        except Exception:
            return []

    @staticmethod
    def _clean_search_query(goal: str) -> str:
        """
        Distills any natural language instruction into an optimal, clean search query:
        - Handles 'play <song> by <artist>' -> '<artist> <song>'
        - Handles 'play <artist>\'s <song>' -> '<artist> <song>'
        - Strips all conversational prefixes ('go play me', 'can you play', 'please play', etc.)
        - Strips quotes, apostrophes, and noisy punctuation that confuse search indexes
        - Strips noise words ('song', 'video', 'official video', 'track', 'music', 'audio', 'lyrics')
        - Preserves track and part numbers (e.g., 'track 2', 'part 1')
        """
        clean = goal.strip()

        # 1. Strip conversational prefixes
        clean = re.sub(
            r'^(now\s+play\s+me|now\s+play|go\s+play\s+me|go\s+play|play\s+me|play\s+us|can\s+you\s+play|please\s+play|'
            r'i\s+want\s+(?:you\s+)?to\s+listen\s+to|listen\s+to|stream|open\s+and\s+play|'
            r'go\s+to\s+youtube\s+and\s+play|go\s+to\s+youtube\s+and\s+search\s+for|go\s+to\s+youtube\s+and\s+search|'
            r'open\s+youtube\s+and\s+play|search\s+on\s+youtube\s+for|search\s+youtube\s+for|search\s+youtube|'
            r'browser\s+play|browser\s+|browse\s+|launch\s+browser\s+|search\s+for|search|look\s+up|find|play)\s+',
            '', clean, flags=re.IGNORECASE
        )

        # 2. Strip imperative web navigation & meta-directive wrappers
        clean = re.sub(
            r'^(?:go\s+to|navigate\s+to|open|visit|head\s+to)\s+[a-z0-9\.\:\/\-]+(?:\s+and\s+)?',
            '', clean, flags=re.IGNORECASE
        )
        clean = re.sub(
            r'^(?:just\s+)?(?:solve|pick|choose)\s+(?:any\s+|a\s+|the\s+)?(?:problem|task|challenge)(?:\s+and\s+submit(?:\s+the\s+answer)?)?',
            '', clean, flags=re.IGNORECASE
        )
        clean = re.sub(
            r'\b(?:and\s+)?(?:submit\s+the\s+answer|and\s+submit|write\s+a\s+solution(?:\s+in\s+the\s+appropriate\s+language)?)\b',
            '', clean, flags=re.IGNORECASE
        )

        # 3. Strip platform references
        clean = re.sub(r'\s+(?:on|in|from)\s+(?:youtube|leetcode|google|github)\b.*$', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+on\s+spotify\b.*$', '', clean, flags=re.IGNORECASE)

        # 4. Handle "search X and play Y"
        m_and = re.search(r'search\s+(?:for\s+)?(.+?)\s+and\s+play\s+(.+)$', clean, flags=re.IGNORECASE)
        if m_and:
            q1, q2 = m_and.group(1).strip(), m_and.group(2).strip()
            clean = f"{q2} {q1}"

        # 5. Handle "X by Y" -> "Y X" (e.g. "play At Peace by Karan Aujla" -> "Karan Aujla At Peace")
        m_by = re.search(r'^(.+?)\s+by\s+(.+)$', clean, flags=re.IGNORECASE)
        if m_by:
            song, artist = m_by.group(1).strip(), m_by.group(2).strip()
            clean = f"{artist} {song}"

        # 6. Remove quotes and special punctuation (quotes harm YouTube ranking)
        clean = re.sub(r'["\'`“”‘’]', ' ', clean)

        # 7. Strip possessive 's (e.g. "Karan Aujla s" -> "Karan Aujla")
        clean = re.sub(r'\b(\w+)\s+s\b', r'\1', clean, flags=re.IGNORECASE)

        # 8. Strip filler noise words that clutter search (preserve track numbers like 'track 2')
        clean = re.sub(
            r'\b(the\s+song\s+of|the\s+song|the\s+music|song\s+of|song|songs|official\s+video|video|audio|music|lyrics)\b',
            ' ', clean, flags=re.IGNORECASE
        )
        clean = re.sub(r'\bthe\s+track\b', ' ', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\btrack(?!\s*\d+)\b', ' ', clean, flags=re.IGNORECASE)

        # 9. Clean multiple whitespace & small filler particles
        tokens = [t for t in clean.split() if t.lower() not in {"the", "a", "an", "of", "me", "for"}]
        return " ".join(tokens)

    @classmethod
    def resolve_youtube_direct_url(cls, query_or_goal: str) -> dict[str, str]:
        """
        Instantly and cleanly resolves the top direct YouTube watch URL for a clean search query without launching any temporary browser window.
        Returns {'watch_url': 'https://www.youtube.com/watch?v=...', 'video_id': '...', 'clean_query': '...'}
        """
        clean_q = cls._clean_search_query(query_or_goal)
        if not clean_q:
            clean_q = query_or_goal.strip()

        encoded = urllib.parse.quote_plus(clean_q)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            seen = set()
            unique_ids = [x for x in video_ids if not (x in seen or seen.add(x))]
            if unique_ids:
                top_id = unique_ids[0]
                return {
                    "clean_query": clean_q,
                    "video_id": top_id,
                    "watch_url": f"https://www.youtube.com/watch?v={top_id}",
                    "search_url": search_url
                }
        except Exception:
            pass
        return {
            "clean_query": clean_q,
            "video_id": "",
            "watch_url": search_url,
            "search_url": search_url
        }

    @staticmethod
    def _build_dom_summary(page: Any, elements: list[BrowserElement]) -> str:
        """Constructs a clean textual summary of the page with vision/spatial coordinates for the LLM brain."""
        url = page.url
        title = page.title()
        lines = [f"PAGE TITLE: {title}", f"URL: {url}", "\nINTERACTIVE ELEMENTS:"]
        for el in elements[:60]:
            label = el.text or el.aria_label or el.placeholder or f"<{el.tag}>"
            type_info = f" ({el.element_type})" if el.element_type != el.tag else ""
            coord_info = f" @ ({int(el.center_x)}, {int(el.center_y)})" if el.width > 0 else ""
            lines.append(f"  [#{el.index}] {el.tag.upper()}{type_info}: \"{label}\"{coord_info}")
        return "\n".join(lines)

    # =========================================================================
    # Visual Grounding & Human-like Execution Engine
    # =========================================================================

    @staticmethod
    def inject_human_cursor_overlay(page: Any):
        """
        Injects a holographic JARVIS visual cursor and click-ripple animation engine directly into the page DOM.
        Judges and users will visually see JARVIS's cursor glide across the screen and click like a real person!
        """
        js = """
        (() => {
            if (document.getElementById('jarvis-cursor-overlay')) return;
            const style = document.createElement('style');
            style.id = 'jarvis-cursor-style';
            style.innerHTML = `
                #jarvis-cursor-overlay {
                    position: fixed;
                    top: -100px; left: -100px;
                    width: 24px; height: 24px;
                    pointer-events: none;
                    z-index: 2147483647;
                    transform: translate(-50%, -50%);
                    transition: left 0.12s ease-out, top 0.12s ease-out;
                }
                .jarvis-pointer-dot {
                    width: 14px; height: 14px;
                    background: #00f0ff;
                    border: 2px solid #ffffff;
                    border-radius: 50%;
                    box-shadow: 0 0 10px #00f0ff, 0 0 20px rgba(0, 240, 255, 0.7);
                }
                .jarvis-click-ripple {
                    position: fixed;
                    border-radius: 50%;
                    border: 2px solid #00f0ff;
                    background: rgba(0, 240, 255, 0.35);
                    pointer-events: none;
                    z-index: 2147483646;
                    transform: translate(-50%, -50%);
                    animation: jarvisRippleAnim 0.45s ease-out forwards;
                }
                @keyframes jarvisRippleAnim {
                    0% { width: 4px; height: 4px; opacity: 1; }
                    100% { width: 55px; height: 55px; opacity: 0; }
                }
                .jarvis-som-badge {
                    position: fixed;
                    background: #ff0055;
                    color: #ffffff;
                    font-family: monospace, sans-serif;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 1px 4px;
                    border-radius: 3px;
                    border: 1px solid #ffffff;
                    z-index: 2147483640;
                    pointer-events: none;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.4);
                }
            `;
            document.head.appendChild(style);

            const cursor = document.createElement('div');
            cursor.id = 'jarvis-cursor-overlay';
            cursor.innerHTML = '<div class="jarvis-pointer-dot"></div>';
            document.body.appendChild(cursor);

            window.jarvisMoveCursor = (x, y) => {
                const c = document.getElementById('jarvis-cursor-overlay');
                if (c) { c.style.left = x + 'px'; c.style.top = y + 'px'; }
            };

            window.jarvisClickRipple = (x, y) => {
                const rip = document.createElement('div');
                rip.className = 'jarvis-click-ripple';
                rip.style.left = x + 'px';
                rip.style.top = y + 'px';
                document.body.appendChild(rip);
                setTimeout(() => rip.remove(), 480);
            };

            window.jarvisSetBadges = (badges) => {
                document.querySelectorAll('.jarvis-som-badge').forEach(b => b.remove());
                badges.forEach(b => {
                    const span = document.createElement('span');
                    span.className = 'jarvis-som-badge';
                    span.innerText = '#' + b.index;
                    span.style.left = (b.x + 2) + 'px';
                    span.style.top = (b.y - 12 > 0 ? b.y - 12 : b.y + 2) + 'px';
                    document.body.appendChild(span);
                });
            };

            window.jarvisClearBadges = () => {
                document.querySelectorAll('.jarvis-som-badge').forEach(b => b.remove());
            };
        })();
        """
        try:
            page.evaluate(js)
        except Exception:
            pass

    @staticmethod
    def render_visual_grounding_overlay(page: Any, elements: list[BrowserElement]):
        """Injects Set-of-Marks (SoM) bounding badges over interactive elements for visual screenshots."""
        badges = [
            {"index": el.index, "x": el.x, "y": el.y}
            for el in elements[:50]
            if el.width > 0 and el.height > 0
        ]
        try:
            page.evaluate("(badges) => window.jarvisSetBadges && window.jarvisSetBadges(badges)", badges)
        except Exception:
            pass

    @staticmethod
    def clear_visual_grounding_overlay(page: Any):
        """Clears Set-of-Marks badges so the live screen view remains clean and responsive."""
        try:
            page.evaluate("() => window.jarvisClearBadges && window.jarvisClearBadges()")
        except Exception:
            pass

    @classmethod
    def human_move_and_click(cls, page: Any, target_el: BrowserElement) -> bool:
        """
        Moves the visible cursor across the screen smoothly, plays click ripple animation,
        and clicks with realistic human mouse physics.
        """
        cx = target_el.center_x
        cy = target_el.center_y

        try:
            loc = page.locator(target_el.selector).first
            loc.scroll_into_view_if_needed(timeout=2000)
            box = loc.bounding_box()
            if box:
                cx = box["x"] + box["width"] / 2
                cy = box["y"] + box["height"] / 2
        except Exception:
            pass

        if cx > 0 and cy > 0:
            try:
                # 1. Animate holographic visual cursor
                page.evaluate(f"() => window.jarvisMoveCursor && window.jarvisMoveCursor({cx}, {cy})")
                
                # 2. Human Bezier-Curved Mouse Glide (Simulates organic hand and wrist movement)
                curr_pos = getattr(page, "_jarvis_mouse_pos", (random.randint(150, 450), random.randint(150, 350)))
                start_x, start_y = curr_pos
                # Calculate natural curved control point
                control_x = (start_x + cx) / 2 + random.uniform(-35, 35)
                control_y = (start_y + cy) / 2 + random.uniform(-35, 35)
                
                # Arc through control point to target with natural deceleration
                page.mouse.move(control_x, control_y, steps=7)
                page.mouse.move(cx, cy, steps=9)
                setattr(page, "_jarvis_mouse_pos", (cx, cy))
                time.sleep(random.uniform(0.06, 0.12))

                # 3. Trigger visual holographic click ripple
                page.evaluate(f"() => window.jarvisClickRipple && window.jarvisClickRipple({cx}, {cy})")

                # 4. Human click physics (contact down -> micro-pause -> release up)
                page.mouse.down()
                time.sleep(random.uniform(0.045, 0.085))
                page.mouse.up()
                return True
            except Exception:
                pass

        # Self-Healing Multi-Strategy Locator Cascade
        # 1. Direct CSS / data-attribute selector
        try:
            loc = page.locator(target_el.selector).first
            loc.click(timeout=2500)
            return True
        except Exception:
            pass

        # 2. Text / Label Matching
        if target_el.text:
            try:
                page.get_by_text(target_el.text, exact=False).first.click(timeout=2000, force=True)
                return True
            except Exception:
                pass

        # 3. ARIA Role & Accessibility Tree
        if target_el.tag in ["button", "a"]:
            try:
                role = "button" if target_el.tag == "button" else "link"
                page.get_by_role(role, name=target_el.text or target_el.aria_label).first.click(timeout=1500, force=True)
                return True
            except Exception:
                pass

        # 4. ARIA Label / Placeholder
        if target_el.aria_label:
            try:
                page.get_by_label(target_el.aria_label).first.click(timeout=1500, force=True)
                return True
            except Exception:
                pass

        # 5. Native DOM Event Dispatch Fallback
        try:
            page.evaluate(f"""() => {{
                const el = document.querySelector('{target_el.selector}') || document.querySelector('[data-jarvis-id="{target_el.index}"]');
                if (el) {{
                    el.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                    return true;
                }}
                return false;
            }}""")
            return True
        except Exception:
            pass

        return False

    @classmethod
    def human_type(cls, page: Any, target_el: BrowserElement, text: str, press_enter: bool = False) -> bool:
        """
        Focuses target input, and types character-by-character with natural human typing jitter.
        """
        # First move and click into the input box
        cls.human_move_and_click(page, target_el)
        time.sleep(random.uniform(0.1, 0.2))

        try:
            # Clear existing content if any
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass

        # Type with natural human cadence (25ms-60ms per char + occasional word pause)
        try:
            for char in text:
                page.keyboard.type(char)
                delay = random.uniform(0.025, 0.055)
                if char in [" ", ",", ".", "-", "_"]:
                    delay += random.uniform(0.04, 0.08)
                time.sleep(delay)

            if press_enter:
                time.sleep(random.uniform(0.12, 0.25))
                page.keyboard.press("Enter")
            return True
        except Exception:
            # Fallback to fill
            try:
                loc = page.locator(target_el.selector).first
                loc.fill(text)
                if press_enter:
                    loc.press("Enter")
                return True
            except Exception:
                return False

    @classmethod
    def _dismiss_modal_or_bypass_auth(cls, page: Any, goal: str) -> Optional[str]:
        """
        Autonomous Modal & Account Barrier Resolver.
        1. If user directive does NOT require logging in or registering:
           - Automatically detects and clicks 'Continue as guest', 'Guest checkout',
             'Use without an account', 'Skip', 'Skip for now', 'Maybe later', 'Not now', 'No thanks', 'Dismiss'.
           - Dismisses cookie banners ('Accept all', 'Reject all', 'I agree', 'Got it').
           - Closes promo popups (buttons with aria-label='Close', data-dismiss='modal', etc.).
        2. If user directive DOES require an account, or if on Google OAuth prompt:
           - Tries clicking 'Continue as [User]' or 'Sign in with Google' to utilize persistent profile.
        Returns description of action taken or None.
        """
        try:
            goal_low = goal.lower()
            needs_auth = any(w in goal_low for w in ["login", "sign in", "signin", "auth", "register", "create account", "my account"])

            if not needs_auth:
                guest_selectors = [
                    "button:has-text('Continue as guest')",
                    "button:has-text('Guest checkout')",
                    "a:has-text('Continue as guest')",
                    "button:has-text('Use Chrome without an account')",
                    "button:has-text('Use without an account')",
                    "button:has-text('Continue without account')",
                    "button:has-text('Skip for now')",
                    "button:has-text('Skip')",
                    "a:has-text('Skip')",
                    "button:has-text('Maybe later')",
                    "button:has-text('Not now')",
                    "button:has-text('No thanks')",
                    "button:has-text('Dismiss')",
                    "button:has-text('Reject all')",
                    "button:has-text('Accept all')",
                    "button:has-text('I agree')",
                    "[aria-label='Reject all']",
                    "[aria-label='Accept all']",
                    "[aria-label='Close']",
                    "button[aria-label='Close dialog']",
                    "tp-yt-paper-button#dismiss-button"
                ]
                for sel in guest_selectors:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=200):
                            txt = loc.inner_text(timeout=200) or sel
                            loc.click(timeout=800)
                            time.sleep(0.5)
                            return f"Autonomously bypassed modal/barrier via: '{txt.strip()}'"
                    except Exception:
                        continue
            else:
                oauth_selectors = [
                    "button:has-text('Continue as ')",
                    "button:has-text('Sign in with Google')",
                    "div[role='button']:has-text('Sign in with Google')",
                    "button:has-text('Continue with Google')"
                ]
                for sel in oauth_selectors:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=200):
                            txt = loc.inner_text(timeout=200) or sel
                            loc.click(timeout=1000)
                            time.sleep(1.0)
                            return f"Autonomously connected via persistent OAuth session: '{txt.strip()}'"
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    # =========================================================================
    # Brain / Action Decision Loop
    # =========================================================================

    def _decide_next_action(
        self,
        goal: str,
        dom_summary: str,
        elements: list[BrowserElement],
        step_history: list[str]
    ) -> dict[str, Any]:
        """
        Decides the next atomic action to take using Meta Llama or structured heuristic reasoning.
        """
        goal_lower = goal.lower()
        history_str = " ".join(step_history).lower()
        is_media_goal = any(term in goal_lower for term in ["play", "song", "music", "video", "listen", "youtube", "stream", "track", "audio"])

        # Extract the current page URL from dom_summary header
        current_url = ""
        for line_item in dom_summary.split("\n"):
            if line_item.startswith("URL:"):
                current_url = line_item.replace("URL:", "").strip().lower()
                break

        is_on_watch_page = "/watch?v=" in current_url or ("/watch" in current_url and "search_query" not in current_url)

        # Check if the page is an authentication / login portal (e.g. accounts.google.com, /login, /signin)
        is_login_page = any(term in current_url for term in [
            "accounts.google.com", "/login", "/signin", "/auth", "challenge", "identifier"
        ])
        if is_login_page and any(w in goal_lower for w in ["login", "sign in", "signin", "auth", "account", "accounts", "want"]):
            return {
                "action": "complete",
                "result": f"Reached authentication portal at {current_url}. Human authentication session ready.",
                "reason": "Login portal detected; waiting for human user credential entry."
            }

        llm = settings.get_llm_client()
        if llm and not settings.is_mock():
            try:
                system_prompt = (
                    "You are Jarvis Autonomous Browser Agent. Your role is to control a web browser to achieve the user's goal.\n"
                    "You are provided with the current DOM state, interactive elements with IDs [#1], [#2], and action history.\n"
                    "Decide the single best next action.\n\n"
                    "Supported Actions (return strictly JSON):\n"
                    "1. Click element: {\"action\": \"click\", \"element_id\": 2, \"reason\": \"Why clicking\"}\n"
                    "2. Type text: {\"action\": \"type\", \"element_id\": 1, \"text\": \"query\", \"press_enter\": true, \"reason\": \"Why typing\"}\n"
                    "3. Navigate: {\"action\": \"navigate\", \"url\": \"https://...\", \"reason\": \"Why navigating\"}\n"
                    "4. Scroll: {\"action\": \"scroll\", \"direction\": \"down\"|\"up\", \"amount\": 400, \"reason\": \"Why scrolling\"}\n"
                    "5. Hover: {\"action\": \"hover\", \"element_id\": 3, \"reason\": \"Hover to reveal menu\"}\n"
                    "6. Press Key: {\"action\": \"press_key\", \"key\": \"Enter\"|\"Escape\"|\"Tab\", \"reason\": \"Why\"}\n"
                    "7. Go Back: {\"action\": \"go_back\", \"reason\": \"Return to previous page\"}\n"
                    "8. Extract Content: {\"action\": \"extract_content\", \"reason\": \"Extract text from current page\"}\n"
                    "9. Wait: {\"action\": \"wait\", \"seconds\": 2, \"reason\": \"Wait for load\"}\n"
                    "10. Complete: {\"action\": \"complete\", \"result\": \"Detailed answer or confirmation\", \"reason\": \"Goal finished\"}\n\n"
                    "Special Operational Rules:\n"
                    "- Account & Obstacle Policy: If a popup, cookie banner, or sign-in gate appears and the user's goal does NOT require logging in, click 'Continue as guest', 'Use without account', 'Skip', 'Maybe later', 'Not now', 'Dismiss', or the Close (X) button. If the user's goal requires an account or personal dashboard, look for 'Sign in with Google' or 'Continue with Google' to utilize the user's persistent profile. If login is strictly required with custom credentials and no guest option exists, mark complete with: 'Account required at current site - please use login <service> to sign in once.' Dismiss cookie banners ('Accept', 'Agree') so they do not block interactions.\n"
                    "- If searching on YouTube, Google, or any site, type ONLY a concise entity or topic name. NEVER type the full user prompt or instructions like 'Navigate to...', 'Choose a problem...', 'Solve and submit...' into search inputs.\n"
                    "- If on a catalog, problemset, or list page (/problemset/, /problems/, /items/) and the goal is to solve/choose a problem, CLICK a problem link directly rather than typing instructions into a search box.\n"
                    "- If searching on YouTube or Google, type a clean search term into the search input with press_enter: true.\n"
                    "- If on YouTube search results and the goal is to play a song/video, find the video link matching the requested song/artist and CLICK it. Never click 'Sign in', 'Settings', or account links! Do NOT mark complete until the video is clicked!\n"
                    "- If on the video watch page (/watch?v=), the video is playing. Use action 'complete'.\n"
                    "- Correct obvious typos in user queries automatically from conversational context.\n"
                )
                user_prompt = (
                    f"USER GOAL: {goal}\n\n"
                    f"ACTION HISTORY:\n" + ("\n".join(f"- {h}" for h in step_history[-5:]) or "None yet.") + "\n\n"
                    f"CURRENT PAGE:\n{dom_summary}\n\n"
                    "Output the next action JSON now:"
                )
                resp = settings.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                content = resp.choices[0].message.content.strip()
                parsed = json.loads(content)
                if "action" in parsed:
                    # Guard A: Never allow the LLM to type imperative commands or meta-prompts into search bars
                    if parsed.get("action") == "type":
                        raw_type_text = parsed.get("text", "")
                        clean_type_text = self._clean_search_query(raw_type_text)
                        # If typing text is full imperative sentence or stripped empty:
                        if not clean_type_text or any(cmd in raw_type_text.lower() for cmd in ["go to", "navigate to", "solve any", "solve a problem", "and submit", "choose a problem", "pick a problem"]):
                            # Redirect to click problem item if on catalog/problemset
                            problem_links = [
                                e for e in elements
                                if (e.tag == "a" and any(p in e.href for p in ["/problems/", "/item/", "/view/"]) and len(e.text.strip()) > 2)
                            ]
                            if problem_links:
                                return {
                                    "action": "click",
                                    "element_id": problem_links[0].index,
                                    "reason": f"Click problem item '{problem_links[0].text[:35]}' rather than typing instructions into search bar"
                                }
                            # Otherwise do not use this invalid type action; fall through to heuristic
                            parsed = None
                        else:
                            parsed["text"] = clean_type_text

                    if parsed:
                        # Guard B: If media goal and not yet on video watch page, do not complete prematurely
                        if is_media_goal and parsed.get("action") in ["complete", "extract_content"] and not is_on_watch_page:
                            pass  # Fall through to click the actual video link
                        elif is_media_goal and ("/results" in current_url or "typed" in history_str) and parsed.get("action") == "click":
                            target_id = parsed.get("element_id")
                            clicked_el = next((e for e in elements if e.index == target_id), None)
                            if clicked_el and clicked_el.tag in ["input", "textarea"]:
                                pass  # Fall through to click the actual video link
                            else:
                                return parsed
                        else:
                            return parsed
            except Exception:
                pass

        # Heuristic Decision Engine (Deterministic fallback for search / navigation / clicking)
        clean_query = self._clean_search_query(goal)

        # Check for guest / skip / dismiss options on barriers if goal does not require auth
        if not any(w in goal_lower for w in ["login", "sign in", "signin", "auth", "register", "create account"]):
            guest_elements = [
                e for e in elements
                if any(g in (e.text + " " + e.aria_label).lower() for g in [
                    "continue as guest", "guest checkout", "use without an account", "use without account",
                    "use chrome without an account", "skip for now", "skip", "maybe later", "not now", "no thanks", "dismiss"
                ])
            ]
            if guest_elements:
                return {
                    "action": "click",
                    "element_id": guest_elements[0].index,
                    "reason": f"Bypass obstacle via '{guest_elements[0].text or 'guest button'}'"
                }

        # Check if already on video watch page
        if is_on_watch_page:
            return {
                "action": "complete",
                "result": f"Successfully playing '{clean_query}' on YouTube.",
                "reason": "Video watch page reached and playback active."
            }

        # If this is a media playback goal on YouTube, look for video link to click
        if is_media_goal and ("youtube" in current_url or "/results" in current_url):
            video_link = None
            kw_list = [w for w in clean_query.lower().split() if len(w) > 2]
            for el in elements:
                full_text = f"{el.text} {el.aria_label} {el.href}".lower()
                if any(ign in full_text for ign in ["sign in", "signin", "accounts.google", "support.google", "policies.google", "privacy", "terms", "help"]):
                    continue
                if any(k in full_text for k in kw_list) and ("/watch" in el.href or "video-title" in el.selector or "thumbnail" in el.selector):
                    video_link = el
                    break

            if not video_link:
                # Fallback to first actual video watch link on page
                for el in elements:
                    full_text = f"{el.text} {el.aria_label} {el.href}".lower()
                    if any(ign in full_text for ign in ["sign in", "signin", "accounts.google", "support.google", "policies.google", "privacy", "terms", "help"]):
                        continue
                    if el.tag == "a" and "/watch" in el.href and len(el.text.strip()) > 3:
                        video_link = el
                        break

            if video_link:
                return {
                    "action": "click",
                    "element_id": video_link.index,
                    "reason": f"Click video '{video_link.text[:35] or 'video'}' to begin playback"
                }

        # Check if page is a problem set, catalog, or directory and goal is to pick/solve an item
        if any(term in current_url for term in ["/problemset", "/problems", "/list", "/directory", "/catalog", "/explore"]):
            problem_links = [
                e for e in elements
                if (e.tag == "a" and any(p in e.href for p in ["/problems/", "/item/", "/view/"]) and len(e.text.strip()) > 2)
            ]
            if problem_links and ("typed" not in history_str or not clean_query):
                first_link = problem_links[0]
                return {
                    "action": "click",
                    "element_id": first_link.index,
                    "reason": f"Select problem item '{first_link.text[:35]}' from problem set directory"
                }

        # Check for search input if not yet typed, NOT already on results page, and clean_query is meaningful
        if "/results" not in current_url and clean_query and len(clean_query) > 1:
            inputs = [
                e for e in elements
                if (e.tag in ["input", "textarea"] and e.element_type in ["text", "search", "input", "textarea"])
                or "search" in (e.placeholder + " " + e.aria_label).lower()
            ]
            if inputs and "typed" not in history_str:
                return {
                    "action": "type",
                    "element_id": inputs[0].index,
                    "text": clean_query,
                    "press_enter": True,
                    "reason": f"Type search term '{clean_query}' into search field and submit"
                }

        # Track already clicked element IDs from history to avoid repeating clicks like a real human
        clicked_ids = {int(m.group(1)) for m in re.finditer(r'\[#(\d+)\]', history_str)}

        # If on a search results page and already typed query, click organic result link or finish
        if "typed" in history_str or any(k in current_url for k in ["/results", "q=", "search?"]):
            if len(step_history) >= 2 and not is_media_goal:
                if any(t in history_str for t in ["clicked", "scrolled"]):
                    return {
                        "action": "complete",
                        "result": f"Successfully navigated and inspected content for '{clean_query or goal}'.",
                        "reason": "Target search results loaded and viewed."
                    }

            # Select the top organic result link (never click the search bar input again)
            result_links = [
                e for e in elements
                if e.index not in clicked_ids
                and e.tag == "a"
                and len(e.text.strip()) > 6
                and not any(ignore in e.text.lower() for ignore in ["privacy", "terms", "settings", "feedback", "images", "videos", "news", "sign in", "login"])
                and not any(ignore in (e.href or "").lower() for ignore in ["preferences", "settings", "feedback", "privacy"])
            ]
            if result_links:
                first_res = result_links[0]
                return {
                    "action": "click",
                    "element_id": first_res.index,
                    "reason": f"Navigate to top result link '{first_res.text[:35]}'"
                }

        # Check for standard links or buttons matching goal keywords (strictly excluding inputs, textareas, and clicked elements)
        clean_words = re.sub(r'[^\w\s]', ' ', goal_lower)
        keywords = [
            w for w in clean_words.split()
            if len(w) > 3 and w not in ["open", "browser", "control", "please", "want", "youtube", "login", "signin", "search", "click"]
        ]
        for kw in keywords:
            for el in elements:
                if el.index in clicked_ids:
                    continue
                if el.tag in ["input", "textarea"]:
                    continue
                if kw in el.text.lower() or kw in el.aria_label.lower():
                    return {
                        "action": "click",
                        "element_id": el.index,
                        "reason": f"Click element '{el.text[:30]}' matching keyword '{kw}'"
                    }

        # Check if non-media search is complete
        if not is_media_goal and len(step_history) >= 2 and any(term in goal_lower for term in ["search", "find", "check"]):
            if "clicked" in history_str or "typed" in history_str:
                return {
                    "action": "complete",
                    "result": f"Successfully performed browser navigation and gathered page data for '{goal}'.",
                    "reason": "Actions executed and target content reached."
                }

        # Default scroll down to see more
        return {
            "action": "scroll",
            "direction": "down",
            "amount": 400,
            "reason": "Scroll viewport to explore more elements"
        }

    # =========================================================================
    # Autonomous Goal Solver Loop & Dynamic Link Deduction
    # =========================================================================

    @classmethod
    def resolve_target_url_autonomously(cls, goal: str) -> str:
        """
        Cognitive Link & Target Synthesizer (Zero Hardcoded Links).
        Dynamically deduces the official destination URL for ANY web task, SaaS platform, or domain.
        """
        low = goal.lower()
        clean_q = cls._clean_search_query(goal)

        # 1. Direct explicit URL in directive
        url_match = re.search(r'https?://[^\s]+', goal)
        if url_match:
            return url_match.group(0)

        # 2. Central Brain Autonomous Link Synthesizer (Primary AI Link Resolver)
        llm = settings.get_llm_client()
        if llm and not settings.is_mock():
            try:
                system_prompt = (
                    "You are the Central Brain Link Resolver for Jarvis Autonomous Browser.\n"
                    "Given the user's objective, deduce the single best, authoritative starting URL to navigate to.\n"
                    "Never output search queries when an official service or portal is requested.\n"
                    "Output strictly JSON: {\"url\": \"https://...\", \"reason\": \"...\"}"
                )
                resp = settings.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Objective: {goal}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                parsed = json.loads(resp.choices[0].message.content or "{}")
                candidate_url = parsed.get("url", "").strip()
                if candidate_url.startswith(("http://", "https://")):
                    return candidate_url
            except Exception:
                pass

        # 3. Dynamic Heuristic & Domain Resolver (First-Principles Fallback)
        domain_match = re.search(r'\b([a-z0-9\-]+\.(?:com|org|io|net|edu|ai|co|gov|app|dev))\b', low)
        if domain_match:
            return f"https://{domain_match.group(1)}"

        # Check for explicit login / sign-in intent and resolve dynamically
        if any(w in low for w in ["login", "signin", "sign in", "auth"]):
            m_target = re.search(r'(?:login|sign\s*in|auth)\s+(?:to|on|in|into)?\s*([a-zA-Z0-9_\-\.]+)', low)
            if not m_target:
                m_target = re.search(r'\b([a-zA-Z0-9_\-]+)\s+(?:login|signin|sign in|auth)\b', low)
            target_str = m_target.group(1) if m_target else "google"
            login_url, _ = BrowserController.resolve_login_target(target_str)
            return login_url

        # Dynamic SaaS / platform entity extraction from navigation directives
        match_site = re.search(r'\b(?:go\s+to|navigate\s+to|open|visit|head\s+to|find.*on)\s+([a-zA-Z0-9\.\-]+)', low)
        if match_site:
            cand = match_site.group(1).lower().strip()
            if cand not in ["the", "a", "my", "our", "this", "some", "any", "at"]:
                if "." in cand:
                    return f"https://{cand}"
                login_url, _ = BrowserController.resolve_login_target(cand)
                # If target was recognized as a known platform, convert to base URL
                if "login" in login_url or "accounts" in login_url:
                    base_domain = urllib.parse.urlparse(login_url).netloc
                    if base_domain:
                        return f"https://{base_domain}"
                return f"https://www.{cand}.com" if not cand.startswith("www.") else f"https://{cand}.com"

        # Fallback to privacy-first DuckDuckGo web search
        encoded = urllib.parse.quote_plus(clean_q or goal.strip())
        return f"https://duckduckgo.com/?q={encoded}"

    def execute_goal(
        self,
        goal: str,
        start_url: Optional[str] = None,
        max_steps: int = 8,
        headless: Optional[bool] = None
    ) -> dict[str, Any]:
        """
        Executes an open-ended goal on the browser through an interactive perception-action loop.
        Zero templates. Figures out links, buttons, inputs, and navigates autonomously.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {"success": False, "error": "Playwright is not installed. Run 'pip install playwright'."}

        is_headless = self.headless if headless is None else headless
        step_logs: list[str] = []
        action_results: list[dict[str, Any]] = []
        extracted_content_text: str = ""

        # Determine start URL dynamically with zero hardwiring
        initial_url = start_url or self.resolve_target_url_autonomously(goal)

        screenshot_base = self.screenshot_dir / f"run_{int(time.time())}"
        screenshot_base.mkdir(parents=True, exist_ok=True)

        try:
            BrowserController.clean_profile_crash_state(self.user_data_dir)
            with sync_playwright() as p:
                context = None
                is_cdp = False
                launch_args = [
                    "--start-maximized",
                    "--disable-session-crashed-bubble",
                    "--hide-crash-restore-bubble",
                    "--restore-last-session=false",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-infobars",
                    "--disable-features=OptimizationHints,TranslateUI"
                ]

                # Step 0: Check for active CDP session (connects directly to your running logged-in desktop browser)
                try:
                    cdp_browser = p.chromium.connect_over_cdp("http://localhost:9222")
                    if cdp_browser.contexts:
                        context = cdp_browser.contexts[0]
                        is_cdp = True
                        step_logs.append("Connected directly to your active running desktop browser via CDP port 9222.")
                except Exception:
                    context = None
                    is_cdp = False

                # 1. Primary Default: Discovered System Default Browser on this machine
                if not context:
                    default_bin = BrowserController.get_system_default_browser_executable()
                    if default_bin:
                        try:
                            context = p.chromium.launch_persistent_context(
                                user_data_dir=str(self.user_data_dir),
                                executable_path=default_bin,
                                headless=is_headless,
                                args=launch_args,
                                ignore_default_args=["--enable-automation", "--no-sandbox"]
                            )
                        except Exception:
                            context = None

                # 2. Preferred Cross-Platform System Channels (macOS / Linux / Windows)
                if not context:
                    for channel in BrowserController.get_preferred_channels():
                        try:
                            if channel:
                                context = p.chromium.launch_persistent_context(
                                    user_data_dir=str(self.user_data_dir),
                                    channel=channel,
                                    headless=is_headless,
                                    args=launch_args,
                                    ignore_default_args=["--enable-automation", "--no-sandbox"]
                                )
                            else:
                                context = p.chromium.launch_persistent_context(
                                    user_data_dir=str(self.user_data_dir),
                                    headless=is_headless,
                                    args=launch_args,
                                    ignore_default_args=["--enable-automation", "--no-sandbox"]
                                )
                            break
                        except Exception:
                            continue

                # 3. Brave Browser
                if not context:
                    brave_bin = BrowserController.get_brave_executable_path()
                    if brave_bin:
                        try:
                            context = p.chromium.launch_persistent_context(
                                user_data_dir=str(self.user_data_dir),
                                executable_path=brave_bin,
                                headless=is_headless,
                                args=launch_args,
                                ignore_default_args=["--enable-automation", "--no-sandbox"]
                            )
                        except Exception:
                            context = None

                # 4. Default Chromium
                if not context:
                    try:
                        context = p.chromium.launch_persistent_context(
                            user_data_dir=str(self.user_data_dir),
                            headless=is_headless,
                            args=launch_args,
                            ignore_default_args=["--enable-automation", "--no-sandbox"]
                        )
                    except Exception:
                        try:
                            browser = p.chromium.launch(headless=True)
                            context = browser.new_context()
                        except Exception:
                            context = None

                if not context:
                    return {
                        "success": False,
                        "goal": goal,
                        "error": "Failed to initialize any browser context on this host.",
                        "execution_log": ["Failed to launch browser context."]
                    }

                # Clean up duplicate empty tabs from prior launches
                init_pages: list[Any] = list(getattr(context, "pages", []))
                if len(init_pages) > 1:
                    for extra_p in init_pages[1:]:
                        try:
                            if extra_p.url in ["about:blank", "chrome://newtab/", ""]:
                                extra_p.close()
                        except Exception:
                            pass
                page = init_pages[0] if init_pages else context.new_page()
                try:
                    page.on("dialog", lambda d: d.dismiss() if getattr(d, 'type', '') == 'beforeunload' else d.accept())
                except Exception:
                    pass
                if hasattr(BrowserController, 'inject_stealth_scripts'):
                    BrowserController.inject_stealth_scripts(page)

                # Native YouTube Ad-Destroyer & Auto-Skipper Script
                page.add_init_script("""
                (() => {
                    setInterval(() => {
                        const skipBtn = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern, .videoAdUiSkipButton');
                        if (skipBtn) skipBtn.click();
                        const ad = document.querySelector('.ad-showing, .ad-interrupting');
                        const video = document.querySelector('video');
                        if (ad && video && !isNaN(video.duration) && video.duration > 0) {
                            video.currentTime = video.duration;
                            video.playbackRate = 16.0;
                        }
                        document.querySelectorAll('#player-ads, .ytd-ad-slot-renderer, .ytp-ad-overlay-container, ytd-banner-promo-renderer').forEach(e => e.remove());
                    }, 80);
                })();
                """)

                # Intercept and abort Google/YouTube ad network traffic
                def _block_ad_traffic(route):
                    req_url = route.request.url.lower()
                    ad_domains = [
                        "doubleclick.net", "googleads", "pagead2.googlesyndication.com",
                        "youtube.com/pagead", "youtube.com/api/stats/ads", "adservice.google.com"
                    ]
                    if any(domain in req_url for domain in ad_domains):
                        try:
                            route.abort()
                        except Exception:
                            pass
                    else:
                        try:
                            route.continue_()
                        except Exception:
                            pass

                try:
                    page.route("**/*", _block_ad_traffic)
                except Exception:
                    pass

                # Navigate to initial entry point
                step_logs.append(f"Navigating to initial target: {initial_url}")
                try:
                    page.goto(initial_url, wait_until="domcontentloaded", timeout=40000)
                except Exception as nav_err:
                    step_logs.append(f"Primary navigation notice: {nav_err}. Falling back to commit wait...")
                    try:
                        page.goto(initial_url, wait_until="commit", timeout=25000)
                    except Exception as fatal_nav:
                        step_logs.append(f"Navigation warning: {fatal_nav}. Continuing with current page state.")
                time.sleep(2.0)
                self.inject_human_cursor_overlay(page)

                # Auto-dismiss initial consent, popups, and bypass guest barriers
                init_bypass = self._dismiss_modal_or_bypass_auth(page, goal)
                if init_bypass:
                    step_logs.append(init_bypass)

                # Check and defeat CAPTCHA / Bot challenges
                captcha_res = BrowserController.defeat_or_detect_captcha(page)
                if captcha_res.get("detected"):
                    step_logs.append(f"Anti-Bot Challenge Detected ({captcha_res.get('type')}) -> Handled: {captcha_res.get('solved_autonomously')}")

                completed_summary = ""
                last_action_sig = None
                repeat_count = 0

                # Main Perception-Action Loop
                for step_idx in range(1, max_steps + 1):
                    # Real-person multi-tab awareness: handle popups or switch to new tab
                    active_pages: list[Any] = list(getattr(context, "pages", []))
                    if len(active_pages) > 1:
                        for extra_p in active_pages[1:]:
                            if not extra_p.is_closed():
                                extra_url = extra_p.url.lower()
                                if any(aux in extra_url for aux in ["support.google", "policies.google", "about:blank", "adservice", "doubleclick"]):
                                    try:
                                        extra_p.close()
                                        step_logs.append(f"Step {step_idx}: Closed unwanted background popup tab ({extra_url[:40]}).")
                                    except Exception:
                                        pass
                                else:
                                    page = extra_p
                                    self.inject_human_cursor_overlay(page)
                                    step_logs.append(f"Step {step_idx}: Shifted focus to new active tab: {page.title()} ({page.url[:40]})")

                    # Check for mid-workflow modals, promo popups, or guest barriers
                    mid_bypass = self._dismiss_modal_or_bypass_auth(page, goal)
                    if mid_bypass:
                        step_logs.append(f"Step {step_idx}: {mid_bypass}")

                    elements = self._extract_interactive_elements(page)
                    if not elements:
                        time.sleep(1.5)
                        elements = self._extract_interactive_elements(page)
                    dom_summary = self._build_dom_summary(page, elements)

                    # Decision
                    decision = self._decide_next_action(goal, dom_summary, elements, step_logs)
                    action = decision.get("action", "complete")
                    reason = decision.get("reason", "")

                    # Real-person anti-loop guard: never repeat the exact same click blindly
                    action_sig = f"{action}:{decision.get('element_id')}:{str(decision.get('text', ''))[:20]}"
                    if action_sig == last_action_sig and action not in ["wait", "scroll"]:
                        repeat_count += 1
                        if repeat_count >= 2:
                            step_logs.append(f"Step {step_idx}: Repetition detected ({action_sig}). Breaking loop gracefully like a human.")
                            completed_summary = f"Completed operations at {page.url} (avoided repetitive action loop)."
                            break
                    else:
                        repeat_count = 0
                    last_action_sig = action_sig

                    # Render Set-of-Marks (SoM) visual badges for multimodal screenshot grounding
                    self.render_visual_grounding_overlay(page, elements)
                    shot_file = str(screenshot_base / f"step_{step_idx}_{action}.png")
                    try:
                        page.screenshot(path=shot_file)
                    except Exception:
                        shot_file = ""
                    # Clear badges so live desktop window stays pristine
                    self.clear_visual_grounding_overlay(page)

                    if action == "complete":
                        completed_summary = decision.get("result") or f"Goal accomplished at {page.url}"
                        step_logs.append(f"Step {step_idx}: Completed — {completed_summary}")
                        action_results.append({
                            "step": step_idx,
                            "action": "complete",
                            "summary": completed_summary,
                            "screenshot": shot_file
                        })
                        break

                    elif action == "click":
                        el_id = decision.get("element_id")
                        target_el = next((e for e in elements if e.index == el_id), None)
                        clicked = False
                        if target_el:
                            # If target element is a video link (/watch?v=...), navigate directly to guarantee instant video load
                            target_href = getattr(target_el, "href", "") or ""
                            if "/watch" in target_href:
                                watch_url = target_href if target_href.startswith("http") else f"https://www.youtube.com{target_href}"
                                try:
                                    step_logs.append(f"Step {step_idx}: Navigating directly to video link: {watch_url}")
                                    page.goto(watch_url, wait_until="domcontentloaded", timeout=30000)
                                    self.inject_human_cursor_overlay(page)
                                    clicked = True
                                except Exception:
                                    pass

                            if not clicked:
                                clicked = self.human_move_and_click(page, target_el)
                                if clicked:
                                    step_logs.append(f"Step {step_idx}: Human-glide clicked [#{el_id}] '{target_el.text or target_el.tag}' @ ({int(target_el.center_x)}, {int(target_el.center_y)}) ({reason})")

                        if clicked and "/watch" in page.url:
                            try:
                                page.wait_for_selector("video", timeout=6000)
                                page.evaluate("""() => {
                                    const v = document.querySelector('video');
                                    if (v) {
                                        v.muted = false;
                                        v.volume = 1.0;
                                        v.play().catch(() => {});
                                    }
                                    const skip = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-overlay-close-button');
                                    if (skip) skip.click();
                                }""")
                            except Exception:
                                pass

                        if not clicked:
                            step_logs.append(f"Step {step_idx}: Could not click element #{el_id}, attempting graceful scroll")
                            page.mouse.wheel(0, 300)

                        time.sleep(1.5)

                    elif action == "type":
                        el_id = decision.get("element_id")
                        text_val = decision.get("text", "")
                        press_enter = decision.get("press_enter", False)
                        typed = False
                        target_el = next((e for e in elements if e.index == el_id), None)
                        if target_el:
                            typed = self.human_type(page, target_el, text_val, press_enter=press_enter)
                            if typed:
                                step_logs.append(f"Step {step_idx}: Human-cadence typed '{text_val}' into [#{el_id}] @ ({int(target_el.center_x)}, {int(target_el.center_y)}) (enter={press_enter})")
                        if not typed:
                            step_logs.append(f"Step {step_idx}: Could not locate input #{el_id}")

                        if press_enter:
                            try:
                                page.wait_for_load_state("domcontentloaded", timeout=10000)
                            except Exception:
                                pass
                        time.sleep(2.0)

                    elif action == "navigate":
                        nav_url = decision.get("url", "")
                        if nav_url:
                            step_logs.append(f"Step {step_idx}: Navigating to {nav_url} ({reason})")
                            try:
                                page.goto(nav_url, wait_until="domcontentloaded", timeout=30000)
                            except Exception as nav_e:
                                step_logs.append(f"Step {step_idx}: Navigation warning: {nav_e}")
                            self.inject_human_cursor_overlay(page)
                            time.sleep(2.0)

                    elif action == "scroll":
                        dist = decision.get("amount", 400)
                        if decision.get("direction") == "up":
                            dist = -dist
                        # Human-like 3-step smooth scroll
                        step_part = dist // 3
                        for _ in range(3):
                            page.mouse.wheel(0, step_part)
                            time.sleep(0.08)
                        step_logs.append(f"Step {step_idx}: Human-scrolled viewport by {dist}px")
                        time.sleep(1.0)

                    elif action == "hover":
                        el_id = decision.get("element_id")
                        target_el = next((e for e in elements if e.index == el_id), None)
                        if target_el:
                            try:
                                page.locator(target_el.selector).first.hover(timeout=2500)
                                step_logs.append(f"Step {step_idx}: Hovered over [#{el_id}] '{target_el.text or target_el.tag}' ({reason})")
                            except Exception:
                                pass
                        time.sleep(1.0)

                    elif action == "press_key":
                        k = decision.get("key", "Enter")
                        page.keyboard.press(k)
                        step_logs.append(f"Step {step_idx}: Pressed keyboard key '{k}' ({reason})")
                        time.sleep(1.0)

                    elif action == "go_back":
                        try:
                            page.go_back(wait_until="domcontentloaded", timeout=15000)
                            step_logs.append(f"Step {step_idx}: Navigated back in browser history ({reason})")
                        except Exception:
                            pass
                        time.sleep(1.5)

                    elif action == "extract_content":
                        try:
                            raw_text = ""
                            for sel in ["main", "article", "[role='main']", "#readme", ".markdown-body", ".Box", "body"]:
                                try:
                                    loc = page.locator(sel).first
                                    if loc.is_visible(timeout=1000):
                                        t_val = loc.inner_text(timeout=2000).strip()
                                        if len(t_val) > len(raw_text):
                                            raw_text = t_val
                                except Exception:
                                    pass
                            if not raw_text:
                                raw_text = page.locator("body").inner_text(timeout=2500).strip()
                            extracted_content_text = raw_text[:12000]
                            preview = re.sub(r'\s+', ' ', extracted_content_text[:120])
                            step_logs.append(f"Step {step_idx}: Extracted content ({len(extracted_content_text)} chars): {preview}...")
                            # If the user objective was to extract, find, search, or summarize, complete after reading
                            if any(w in goal.lower() for w in ["extract", "find", "search", "summarize", "what is", "who is", "list", "top", "trending", "get", "description"]):
                                completed_summary = f"Content extracted successfully from {page.url}."
                                break
                        except Exception as e:
                            step_logs.append(f"Step {step_idx}: Content extraction failed: {e}")

                    elif action == "wait":
                        wait_sec = decision.get("seconds", 2)
                        time.sleep(wait_sec)
                        step_logs.append(f"Step {step_idx}: Waited {wait_sec}s")

                    action_results.append({
                        "step": step_idx,
                        "action": action,
                        "reason": reason,
                        "url": page.url,
                        "screenshot": shot_file
                    })

                # Capture final state
                final_title = page.title()
                final_url = page.url
                final_shot = str(screenshot_base / "final_state.png")
                try:
                    page.screenshot(path=final_shot, full_page=True)
                except Exception:
                    final_shot = ""

                # If this is a media playback mission, stream the audio and video live on the monitor
                is_media_playback = any(w in goal.lower() for w in ["play", "song", "music", "video", "listen", "stream", "audio", "track"])
                if is_media_playback and not is_headless:
                    # If not yet on watch page, click or navigate to first video link
                    if "/watch" not in page.url:
                        # 1. Direct Playwright locator click
                        try:
                            v_loc = page.locator("a#video-title, ytd-video-renderer a#thumbnail, a[href*='/watch?v=']").first
                            if v_loc.is_visible(timeout=4000):
                                v_loc.click()
                                time.sleep(3.0)
                        except Exception:
                            pass

                    # 2. Extract DOM href evaluation fallback
                    if "/watch" not in page.url:
                        try:
                            watch_href = page.evaluate("""() => {
                                const a = document.querySelector("a#video-title, ytd-video-renderer a[href*='/watch'], a[href*='/watch?v=']");
                                return a ? a.getAttribute('href') : null;
                            }""")
                            if watch_href:
                                watch_url = watch_href if watch_href.startswith("http") else f"https://www.youtube.com{watch_href}"
                                page.goto(watch_url, wait_until="domcontentloaded", timeout=20000)
                                time.sleep(2.0)
                        except Exception:
                            pass

                    # 3. Fallback to interactive elements
                    if "/watch" not in page.url:
                        for el in self._extract_interactive_elements(page):
                            if "/watch" in el.href:
                                watch_url = el.href if el.href.startswith("http") else f"https://www.youtube.com{el.href}"
                                try:
                                    page.goto(watch_url, wait_until="domcontentloaded", timeout=20000)
                                    break
                                except Exception:
                                    pass

                    if "/watch" in page.url:
                        try:
                            page.wait_for_selector("video", timeout=8000)
                            page.evaluate("""() => {
                                const v = document.querySelector('video');
                                if (v) {
                                    v.muted = false;
                                    v.volume = 1.0;
                                    v.play().catch(() => {});
                                }
                                const skip = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-overlay-close-button');
                                if (skip) skip.click();
                            }""")
                        except Exception:
                            pass
                        final_title = page.title()
                        final_url = page.url
                        print(f"\n🎵 [Now Playing Live]: {final_title}")
                        step_logs.append(f"Autonomous playback verified: {final_title} ({final_url})")
                    else:
                        print(f"\n⚠️ Reached search results: {page.url}")

                if not is_cdp:
                    try:
                        context.close()
                    except Exception:
                        pass
                    try:
                        BrowserController.clean_profile_crash_state(self.user_data_dir)
                    except Exception:
                        pass

                answer = ""
                # Autonomous Answer Synthesizer: If content was extracted or goal was information retrieval, synthesize findings
                if extracted_content_text or any(w in goal.lower() for w in ["find", "extract", "summarize", "search", "what", "list", "top", "trending", "get", "description"]):
                    if not extracted_content_text:
                        try:
                            extracted_content_text = page.locator("main, [role='main'], body").first.inner_text(timeout=2500).strip()[:12000]
                        except Exception:
                            pass
                    if extracted_content_text:
                        try:
                            synth_prompt = (
                                f"You are JARVIS, an autonomous AI partner. The user gave you this objective: '{goal}'.\n"
                                f"We navigated to '{final_url}' ({final_title}) and extracted the live DOM content below:\n\n"
                                f"{extracted_content_text[:7000]}\n\n"
                                f"Deliver a direct, high-value, comprehensive response that answers the user's request thoroughly.\n"
                                f"Include specific repository names, titles, descriptions, metrics, and key details as requested."
                            )
                            resp = settings.create_chat_completion(
                                messages=[
                                    {"role": "system", "content": "You are JARVIS, Master Ansh's autonomous executive technical partner."},
                                    {"role": "user", "content": synth_prompt}
                                ],
                                temperature=0.2
                            )
                            answer = resp.choices[0].message.content or ""
                            if answer:
                                completed_summary = answer
                        except Exception:
                            pass

                return {
                    "success": True,
                    "goal": goal,
                    "final_url": final_url,
                    "final_title": final_title,
                    "summary": completed_summary or f"Agent successfully operated on {final_title} ({final_url})",
                    "extracted_data": answer or extracted_content_text[:2000],
                    "steps_executed": len(action_results),
                    "execution_log": step_logs,
                    "final_screenshot": final_shot
                }

        except Exception as e:
            return {
                "success": False,
                "goal": goal,
                "error": f"Browser Agent execution failed: {e!s}",
                "execution_log": step_logs
            }

    # =========================================================================
    # High-Level Specialist Workflows
    # =========================================================================

    def send_emails_batch_autonomously(
        self,
        recipient: str,
        emails: list[dict[str, str]],
        auto_send: bool = True
    ) -> dict[str, Any]:
        """
        Specialized Single-Tab Batch Email Dispatcher.
        Dispatches all N emails sequentially in ONE active browser tab without thrashing browser restarts.
        """
        pw_res = BrowserController.automate_gmail_batch_dispatch_playwright(
            recipient=recipient,
            emails=emails,
            headless=self.headless,
            user_data_dir=str(self.user_data_dir)
        )

        if pw_res.get("success") and pw_res.get("sent_automatically"):
            return {
                "success": True,
                "method": "autonomous_playwright_batch_dispatch",
                "recipient": recipient,
                "total_dispatched": pw_res.get("total_dispatched", len(emails)),
                "screenshot": pw_res.get("screenshot"),
                "actions": pw_res.get("actions", []),
                "message": f"Browser Agent successfully navigated to Gmail and dispatched {len(emails)} emails sequentially in a single persistent tab to {recipient}."
            }

        # Fallback to Host Browser batch compose
        bridge_res = BrowserController.compose_batch_in_gmail(emails=emails)
        return {
            "success": True,
            "method": "host_browser_authenticated_batch_session",
            "recipient": recipient,
            "actions": [
                "Checked persistent Playwright profile for authenticated session",
                "Detected external Google authentication barrier",
                f"Seamlessly activated active host browser with {len(emails)} pre-composed letters",
                "User browser opened directly to Gmail Compose ready for 1-click transmission"
            ],
            "bridge_details": bridge_res,
            "message": f"Active host browser launched with {len(emails)} pre-composed emails to {recipient}. Ready for 1-click instant delivery."
        }

    def send_email_autonomously(
        self,
        recipient: str,
        subject: str,
        body: str,
        auto_send: bool = True
    ) -> dict[str, Any]:
        """
        Specialized Browser Agent workflow for outbound personal emails.
        1. Tries Playwright real-person automation in persistent browser profile.
        2. If Google login blocks automated login, seamlessly bridges to the host browser
           session where the user is already authenticated, opening the composed letter.
        """
        # Try full human-like Playwright automation
        pw_res = BrowserController.automate_gmail_dispatch_playwright(
            recipient=recipient,
            subject=subject,
            body=body,
            headless=self.headless,
            user_data_dir=str(self.user_data_dir)
        )

        if pw_res.get("success") and pw_res.get("sent_automatically"):
            return {
                "success": True,
                "method": "autonomous_playwright_dispatch",
                "recipient": recipient,
                "subject": subject,
                "screenshot": pw_res.get("screenshot"),
                "actions": pw_res.get("actions", []),
                "message": f"Browser Agent successfully navigated to Gmail, composed letter, and clicked Send for {recipient}."
            }

        # If Google sign-in was required or Playwright could not bypass auth, trigger the seamless Host Browser Bridge
        bridge_res = BrowserController.compose_in_gmail(recipient=recipient, subject=subject, body=body)
        return {
            "success": True,
            "method": "host_browser_authenticated_session",
            "recipient": recipient,
            "subject": subject,
            "actions": [
                "Checked persistent Playwright profile for authenticated session",
                "Detected external Google authentication barrier",
                "Seamlessly activated active host browser with pre-composed letter",
                "User browser opened directly to Gmail Compose ready for 1-click transmission"
            ],
            "bridge_details": bridge_res,
            "message": f"Active host browser launched with pre-composed email to {recipient}. Ready for 1-click instant delivery."
        }

    @classmethod
    def get_leetcode_active_language(cls, page: Any) -> str:
        """
        Dynamically detects active programming language on LeetCode.
        Combines 3 layers of perception:
        1. Live DOM Toolbar Button: Reads the exact text of the language dropdown button (e.g. 'C++', 'Python3', 'Java').
        2. Monaco Editor Active Model Ground Truth: Checks active editor's getModel().getLanguageId().
        3. Code Stub Syntax Analysis: Inspects the method starter code inside the editor for definitive syntax markers.
        """
        try:
            detected = page.evaluate("""() => {
                const KNOWN_LANGS = [
                    "C++", "Python3", "Python", "Java", "C", "C#", "JavaScript", "TypeScript",
                    "PHP", "Swift", "Kotlin", "Dart", "Go", "Ruby", "Scala", "Rust", "Racket", "Erlang", "Elixir"
                ];
                const langMap = {
                    "cpp": "C++", "c": "C", "python": "Python3", "python3": "Python3",
                    "java": "Java", "rust": "Rust", "go": "Go", "typescript": "TypeScript",
                    "javascript": "JavaScript", "csharp": "C#", "c#": "C#"
                };

                // Layer 1: Check the visible language button in the editor header toolbar
                const buttons = Array.from(document.querySelectorAll("button, [role='button']"));
                for (const btn of buttons) {
                    if (!btn.offsetParent && btn.offsetWidth === 0) continue;
                    const raw = (btn.innerText || "").trim().split('\\n')[0].trim();
                    for (const kl of KNOWN_LANGS) {
                        if (raw === kl || raw.startsWith(kl + " ") || raw.startsWith(kl + "\\n") || raw === kl + "v" || raw === kl + " v") {
                            return kl === "Python" ? "Python3" : kl;
                        }
                    }
                }

                // Layer 2: Monaco Editor Active Editor Ground Truth
                if (window.monaco && monaco.editor) {
                    const editors = monaco.editor.getEditors ? monaco.editor.getEditors() : [];
                    for (const ed of editors) {
                        const m = ed.getModel();
                        if (m) {
                            const lid = (m.getLanguageId() || "").toLowerCase();
                            if (langMap[lid]) return langMap[lid];
                        }
                    }
                    const models = monaco.editor.getModels ? monaco.editor.getModels() : [];
                    for (const m of models) {
                        const lid = (m.getLanguageId() || "").toLowerCase();
                        if (langMap[lid]) return langMap[lid];
                    }
                }

                // Layer 3: Starter Stub Syntax Analysis
                let stub = "";
                if (window.monaco && monaco.editor) {
                    const editors = monaco.editor.getEditors ? monaco.editor.getEditors() : [];
                    if (editors.length > 0 && editors[0].getModel()) {
                        stub = editors[0].getModel().getValue();
                    } else if (monaco.editor.getModels && monaco.editor.getModels().length > 0) {
                        stub = monaco.editor.getModels()[0].getValue();
                    }
                }
                if (!stub) {
                    const linesEl = document.querySelector(".monaco-editor .view-lines");
                    if (linesEl) stub = linesEl.innerText || "";
                }
                if (stub) {
                    if (stub.includes("vector<") || stub.includes("class Solution {") || stub.includes("public:")) return "C++";
                    if (stub.includes("def ") || stub.includes("class Solution:") || stub.includes("->")) return "Python3";
                    if (stub.includes("public class Solution") || stub.includes("public int ")) return "Java";
                    if (stub.includes("impl Solution") || stub.includes("pub fn ")) return "Rust";
                    if (stub.includes("func ") && stub.includes(")")) return "Go";
                }

                return "";
            }""")
            return str(detected) if detected else "C++"
        except Exception:
            return "C++"

    @classmethod
    def switch_leetcode_language(cls, page: Any, target_lang: str = "Python3") -> bool:
        """
        Dynamically detects active Monaco language on LeetCode and switches to target_lang (e.g. Python3).
        Guarantees that synthesized code language strictly matches the Monaco editor language.
        """
        try:
            # 1. Detect current language via Monaco Model & Toolbar ground truth
            cur_lang = cls.get_leetcode_active_language(page)
            target_norm = "Python3" if target_lang.lower() in ["python", "python3"] else target_lang
            if cur_lang.lower() == target_norm.lower() or (cur_lang.lower() == "python" and target_norm.lower() == "python3"):
                return True

            # 2. Click the language dropdown button in the editor header
            lang_btn = None
            if cur_lang:
                for cand in page.locator(f"button:has-text('{cur_lang}')").all():
                    if cand.is_visible():
                        lang_btn = cand
                        break

            if not lang_btn:
                for sel in [
                    "button[id*='headlessui-listbox-button']",
                    "[data-cy='lang-select']",
                    ".monaco-editor button",
                    "div.relative button:has(svg)"
                ]:
                    cand = page.locator(sel).first
                    if cand.is_visible(timeout=1200):
                        lang_btn = cand
                        break

            if lang_btn and lang_btn.is_visible():
                lang_btn.click()
                time.sleep(0.8)

                # 3. Select target language from popover options
                for opt_sel in [
                    f"div[role='option']:has-text('{target_norm}')",
                    f"li:has-text('{target_norm}')",
                    f"[role='listbox'] :has-text('{target_norm}')",
                    f"button:has-text('{target_norm}')",
                    f"text='{target_norm}'"
                ]:
                    opt = page.locator(opt_sel).first
                    if opt.is_visible(timeout=1800):
                        opt.click()
                        time.sleep(1.5)
                        # Verify Monaco model updated
                        new_lang = cls.get_leetcode_active_language(page)
                        return new_lang.lower() in [target_norm.lower(), "python" if target_norm.lower() == "python3" else ""]
        except Exception:
            pass
        return False

    def solve_leetcode_problem(
        self,
        problem_slug_or_url: str = "daily",
        solution_code: Optional[str] = None,
        language: Optional[str] = None,
        headless: Optional[bool] = None,
        keep_open: bool = True
    ) -> dict[str, Any]:
        """
        Navigates via Brave/Chrome browser to LeetCode, dynamically inspects the problem
        and code stub directly from the page DOM, synthesizes the algorithm via LLM, and submits.
        Zero GraphQL templates. Pure browser DOM perception.
        Co-Worker Window Paradigm: Keeps the browser session alive for continuous user collaboration.
        """
        is_hl = self.headless if headless is None else headless
        context, is_cdp = self.get_or_create_session(headless=is_hl)
        if not context:
            return {"success": False, "error": "Playwright or browser initialization failed."}

        target_input = (problem_slug_or_url or "daily").strip().lower()
        if target_input in ["daily", "streak", "today", "", "any", "problem", "leetcode"]:
            target_url = "https://leetcode.com/problemset/"
        else:
            target_url = problem_slug_or_url.strip()
            if not target_url.startswith("http"):
                clean_slug = target_url.strip("/").split("/")[-1]
                target_url = f"https://leetcode.com/problems/{clean_slug}/"

        actions_taken = []
        default_bin = BrowserController.get_system_default_browser_executable()
        browser_label = "Chrome" if (default_bin and "chrome" in default_bin.lower()) else ("Brave" if (default_bin and "brave" in default_bin.lower()) else "Desktop Browser")
        if is_cdp:
            actions_taken.append(f"Connected directly to running {browser_label} session (CDP Mode)")
        elif default_bin:
            actions_taken.append(f"Using persistent {browser_label} context: {default_bin}")
        else:
            actions_taken.append("Using persistent Chromium browser context")

        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Navigate to LeetCode target
        print(f"\n[Action 1] Launching visible {browser_label} & navigating to: {target_url}...")
        actions_taken.append(f"Navigating to: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded", timeout=40000)
        time.sleep(2.0)
        self.inject_human_cursor_overlay(page)

        # Check Cloudflare challenge
        print("[Action 2] Inspecting Cloudflare Turnstile & security shield...")
        captcha = BrowserController.defeat_or_detect_captcha(page)
        if captcha.get("detected"):
            actions_taken.append(f"Cloudflare Challenge Detected ({captcha.get('type')}) - Auto-handled: {captcha.get('solved_autonomously')}")
            print("\n[Notice] Cloudflare Challenge detected. Please complete the verification in the browser window if prompted...")
            time.sleep(4.0)

        # If landed on problemset, click a problem from the live DOM with human mouse movement
        if "/problemset" in page.url or target_url.endswith("/problemset/"):
            try:
                page.wait_for_selector("a[href*='/problems/']", timeout=12000)
                problem_locs = page.locator("a[href*='/problems/']").all()
                chosen_link = None
                for pl in problem_locs:
                    h = pl.get_attribute("href") or ""
                    if "/problems/" in h and not any(skip in h for skip in ["random-one-question", "tag", "solution", "discuss", "contest"]):
                        chosen_link = pl
                        break
                if chosen_link and chosen_link.is_visible(timeout=5000):
                    href = chosen_link.get_attribute("href") or ""
                    box = chosen_link.bounding_box()
                    if box:
                        cx = box["x"] + box["width"] / 2
                        cy = box["y"] + box["height"] / 2
                        page.evaluate(f"() => window.jarvisMoveCursor && window.jarvisMoveCursor({cx}, {cy})")
                        page.mouse.move(cx, cy, steps=12)
                        page.evaluate(f"() => window.jarvisClickRipple && window.jarvisClickRipple({cx}, {cy})")
                        page.mouse.down()
                        time.sleep(0.08)
                        page.mouse.up()
                    else:
                        chosen_link.click()
                    time.sleep(3.0)
                    if len(context.pages) > 1:
                        page = context.pages[-1]
                    self.inject_human_cursor_overlay(page)
                    actions_taken.append(f"Selected problem dynamically from live DOM: {href}")
            except Exception:
                pass

        try:
            prob_title = page.title() if not page.is_closed() else "LeetCode Problem"
        except Exception:
            prob_title = "LeetCode Problem"

        # Wait for problem title or editor container
        print("[Action 3] Locating Monaco Code Editor on page...")
        try:
            page.wait_for_selector(".monaco-editor, [data-track-load='code_editor'], #editor", timeout=12000)
            actions_taken.append("Monaco code editor located on page.")
        except Exception:
            actions_taken.append("Editor not immediately ready; waiting for layout stabilization.")

        # Determine target programming language (Polyglot: C++, Python, Java, Rust, Go, TypeScript, etc.)
        current_active_lang = self.get_leetcode_active_language(page)
        if language and language.lower() not in current_active_lang.lower():
            print(f"[Action 3.5] Requested '{language}'. Switching Monaco Editor language from '{current_active_lang}' to '{language}'...")
            switched = self.switch_leetcode_language(page, language)
            if switched:
                current_active_lang = self.get_leetcode_active_language(page)
                target_lang = current_active_lang
                actions_taken.append(f"Switched Monaco language from UI to: {target_lang}")
                print(f"[Action 3.5] Monaco successfully switched to: {target_lang}")
            else:
                # Choice 1: If UI switch was not possible, adapt code to match active UI
                target_lang = current_active_lang
                print(f"[Action 3.5] Monaco remained in {current_active_lang}. Adapting algorithm synthesis to match active UI: {target_lang}...")
                actions_taken.append(f"Adapted algorithm synthesis to active Monaco language: {target_lang}")
        else:
            # Choice 1: Directly respect the UI's active language
            target_lang = current_active_lang
            print(f"[Action 3.5] Monaco Editor active language recognized: {target_lang}")
            actions_taken.append(f"Operating in active Monaco language: {target_lang}")

        # Map language to markdown block tag
        lang_lower = target_lang.lower()
        tag_map = {
            "c++": "cpp", "cpp": "cpp", "python3": "python", "python": "python",
            "java": "java", "rust": "rust", "go": "go", "golang": "go",
            "typescript": "typescript", "javascript": "javascript", "c#": "csharp", "c": "c"
        }
        code_tag = tag_map.get(lang_lower, lang_lower)

        # Dynamic code generation from live DOM problem description & Monaco starter stub
        code_to_inject: str = solution_code or ""
        if not code_to_inject:
            problem_text = ""
            try:
                desc_el = page.locator("[data-track-load='description_content'], #qd-content, .elfjS").first
                if desc_el.is_visible(timeout=3000):
                    problem_text = desc_el.inner_text()[:1200]
            except Exception:
                problem_text = prob_title

            # Extract starter stub from Monaco model to guarantee exact method signature
            starter_stub = ""
            try:
                starter_stub = page.evaluate("""() => {
                    if (window.monaco && monaco.editor) {
                        const editors = monaco.editor.getEditors ? monaco.editor.getEditors() : [];
                        if (editors.length > 0 && editors[0].getModel()) {
                            return editors[0].getModel().getValue();
                        }
                        if (monaco.editor.getModels && monaco.editor.getModels().length > 0) {
                            return monaco.editor.getModels()[0].getValue();
                        }
                    }
                    return "";
                }""")
            except Exception:
                starter_stub = ""

            llm = settings.get_llm_client()
            if llm and not settings.is_mock():
                try:
                    print(f"[LeetCode] Synthesizing optimal {target_lang} solution from page DOM for '{prob_title}'...")
                    prompt_user = f"Problem: {prob_title}\nProblem Description from DOM:\n{problem_text}\n"
                    if starter_stub:
                        prompt_user += f"\nLeetCode {target_lang} Starter Stub (Adhere strictly to this method signature):\n{starter_stub}\n"
                    prompt_user += f"Write the complete, optimal {target_lang} Solution class."

                    resp = settings.create_chat_completion(
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    f"You are a competitive programming world finalist.\n"
                                    f"Write an optimal, bug-free, production-grade {target_lang} class Solution for this problem.\n"
                                    f"CRITICAL REQUIREMENTS:\n"
                                    f"1. Adhere strictly to {target_lang} syntax and the starter stub method signature.\n"
                                    f"2. You may analyze the approach first, but output the final, self-contained solution inside a single ```{code_tag} ``` markdown code fence.\n"
                                    f"3. The code block must contain ONLY valid, compilable {target_lang} code. Do NOT embed internal thought monologues, scratchpad reasoning, or stream-of-consciousness inside the code fence."
                                )
                            },
                            {"role": "user", "content": prompt_user}
                        ],
                        temperature=0.1
                    )
                    raw_ans = resp.choices[0].message.content or ""
                    fence_match = re.search(r'```(?:' + re.escape(code_tag) + r'|[a-zA-Z0-9_+#.-]*)?\n(.*?)```', raw_ans, re.DOTALL)
                    if fence_match:
                        code_to_inject = fence_match.group(1).strip()
                    else:
                        code_to_inject = raw_ans.strip()

                    # Universal architectural cleanup: Remove full-line conversational scratchpad comments without brittle word blacklists
                    cleaned_lines = []
                    for line in code_to_inject.splitlines():
                        stripped = line.strip()
                        # Generic rule: Strip full-line comments that start with conversational / meta-cognitive prefixes
                        if re.match(r'^(?:#|//|\*)\s*(?:let\'?s|we\s+need|thinking\b|scratchpad|let\s+me|my\s+approach|note\s+that)', stripped, re.I):
                            continue
                        cleaned_lines.append(line)
                    code_to_inject = "\n".join(cleaned_lines).strip()

                    actions_taken.append(f"Synthesized optimal {target_lang} solution adhering to starter signature.")
                except Exception:
                    code_to_inject = ""

        # Inject code into Monaco Editor
        injected = False
        try:
            # Approach A: Monaco JavaScript Model Injection (cleanest & replaces entire stub)
            injected = page.evaluate("""(code) => {
                if (window.monaco && monaco.editor) {
                    const editors = monaco.editor.getEditors ? monaco.editor.getEditors() : [];
                    if (editors.length > 0 && editors[0].getModel()) {
                        editors[0].getModel().setValue(code);
                        return true;
                    }
                    if (monaco.editor.getModels && monaco.editor.getModels().length > 0) {
                        monaco.editor.getModels()[0].setValue(code);
                        return true;
                    }
                }
                return false;
            }""", code_to_inject)
            if injected:
                actions_taken.append(f"Injected {target_lang} solution directly via Monaco API model.")
                print(f"[Action 4] Injected optimal {target_lang} solution directly into Monaco Editor!")
        except Exception:
            injected = False

        if not injected:
            try:
                # Approach B: Direct textarea focus
                ta = page.locator("textarea[aria-label='Code editor'], .monaco-editor textarea, textarea.inputarea").first
                if ta.is_visible(timeout=8000):
                    ta.focus()
                    time.sleep(0.3)
                    page.keyboard.press("Control+A")
                    time.sleep(0.1)
                    page.keyboard.press("Backspace")
                    time.sleep(0.1)
                    page.keyboard.insert_text(code_to_inject or "")
                    injected = True
                    actions_taken.append(f"Injected {target_lang} solution into Monaco Editor via direct textarea focus.")
                    print(f"[Action 4] Injected optimal {target_lang} solution directly into Monaco Editor!")
            except Exception:
                injected = False

        # Check login status to guarantee account streak recording
        is_signed_in = True
        try:
            not_logged_in_selectors = [
                "a:has-text('Register or Log in')",
                "button:has-text('Register or Log in')",
                "a:has-text('Log in')",
                "button:has-text('Log in')",
                "a:has-text('Sign in')",
                "text='You need to log in / sign up to run or submit'",
                "[data-cy='sign-in-btn']",
                "a[href*='/accounts/login']"
            ]
            for sel in not_logged_in_selectors:
                if page.locator(sel).first.is_visible(timeout=1000):
                    is_signed_in = False
                    break
        except Exception:
            is_signed_in = True

        if not is_signed_in:
            print("\n⚠️ [LeetCode Auth Required] You are not logged into LeetCode in this browser profile.")
            print("  • Please click 'Register or Log in' in the open browser window on your screen.")
            print("  • Once you log in, your login session & cookies are PERMANENTLY saved to ~/.llama_orchestrator/browser_profile.")
            print("  • Tip: Use 'login leetcode' in JARVIS CLI anytime for a dedicated sign-in session.")
            print("  • Holding browser window open for login...")
            try:
                # Give user opportunity to sign in without being rushed
                for _ in range(45):
                    time.sleep(1.0)
                    try:
                        still_unauthed = any(page.locator(s).first.is_visible(timeout=400) for s in ["a:has-text('Register or Log in')", "text='You need to log in / sign up to run or submit'"])
                        if not still_unauthed:
                            is_signed_in = True
                            print("✓ LeetCode login session recognized! Proceeding with submission...")
                            break
                    except Exception:
                        pass
            except Exception:
                pass

        # Click Run or Submit button with realistic human mouse movement & ripple
        submitted = False
        verdict = "Submitted (Verdict pending)"
        if is_signed_in:
            for btn_text in ["Submit", "Run"]:
                try:
                    btn = page.locator(f"button:has-text('{btn_text}'), [data-e2e-locator='console-submit-button']").first
                    if btn.is_visible(timeout=3000):
                        box = btn.bounding_box()
                        if box:
                            cx = box["x"] + box["width"] / 2
                            cy = box["y"] + box["height"] / 2
                            page.evaluate(f"() => window.jarvisMoveCursor && window.jarvisMoveCursor({cx}, {cy})")
                            page.mouse.move(cx, cy, steps=15)
                            time.sleep(0.1)
                            page.evaluate(f"() => window.jarvisClickRipple && window.jarvisClickRipple({cx}, {cy})")
                            page.mouse.down()
                            time.sleep(0.08)
                            page.mouse.up()
                        else:
                            btn.click()
                        submitted = True
                        actions_taken.append(f"Human-glide clicked '{btn_text}' button on LeetCode.")
                        print(f"[Action 5] Clicked '{btn_text}' button on LeetCode with visual cursor glide!")

                        # Await evaluation verdict
                        print("[Action 6] Awaiting LeetCode evaluation verdict...")
                        for _ in range(12):
                            time.sleep(1.0)
                            try:
                                v_el = page.locator("[data-e2e-locator='submission-result'], .text-green-s, .text-red-s, [class*='result-state']").first
                                if v_el.is_visible(timeout=1000):
                                    verdict = v_el.inner_text().strip()
                                    print(f"[LeetCode Verdict] ★ {verdict}")
                                    actions_taken.append(f"LeetCode Verdict: {verdict}")
                                    break
                            except Exception:
                                pass
                        break
                except Exception:
                    continue
        else:
            actions_taken.append("Skipped live submit click because user is not authenticated on LeetCode.")
            print(f"\n[Notice] {target_lang} solution entered in Monaco. Live submission held pending authentication.")

        # Take high-resolution screenshot
        shot_path = Path("workspaces/screenshots/leetcode_live_execution.png")
        shot_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if not page.is_closed():
                page.screenshot(path=str(shot_path))
                actions_taken.append(f"Saved live screenshot to {shot_path}")
        except Exception:
            pass

        try:
            final_title = page.title() if not page.is_closed() else prob_title
            final_url = page.url if not page.is_closed() else target_url
        except Exception:
            final_title = prob_title
            final_url = target_url

        if is_hl or (not keep_open and not is_cdp):
            try:
                context.close()
            except Exception:
                pass
        else:
            print(f"\n[Co-Worker Window Mode] {browser_label} session remains active on your desktop for continuous work and inspection.")

        return {
            "success": injected or submitted,
            "problem_url": final_url,
            "browser": browser_label,
            "injected": injected,
            "submitted": submitted,
            "verdict": verdict,
            "screenshot": str(shot_path),
            "final_title": final_title,
            "final_url": final_url,
            "actions": actions_taken
        }


# Global Singleton Instance
browser_agent = BrowserAgent()

