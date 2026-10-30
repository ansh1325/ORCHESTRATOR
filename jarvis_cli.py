#!/usr/bin/env python3
"""
Jarvis Autonomous Multi-Agent OS — Command-Line Interface (CLI)
Creator: Ansh Tiwari (Chief Distributed Systems Architect)

Provides 100% full-fidelity access to all Jarvis capabilities directly in the terminal:
- Real-time Conversational Brain & Reasoning
- Windows Native Voice Synthesis (Audio Spoken Output)
- 5-Stage Autonomous Multi-Agent Swarm Lifecycle
- Interactive Clarifying Questions & Knowledge Base Synthesis
- Direct System Browser Automation (Gmail u/0 inbox, compose, and Playwright actions)
- Session History, Workspaces, and Host File Exports
"""

import asyncio
import json
import os
import re
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Optional

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure robust UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.autonomous_solver import CreativeProblemSolver, StrategicOutreachArchitect, PortSafetyGuard
from core.browser_controller import BrowserController
from core.creator_memory import creator_memory
from core.models import ExecutionEvent, IntentAnalysis
from core.orchestrator import orchestrator
from core.workflow_manager import workflow_manager

# Terminal Colors & Styling
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BG_BLUE = "\033[44m"


class JarvisCLI:
    def __init__(self):
        self.voice_enabled: bool = True
        self.active_session_id: Optional[str] = None
        self._speech_lock = threading.Lock()

    def speak(self, text: str):
        """Speaks text aloud using Windows Native Speech Synthesis asynchronously."""
        if not self.voice_enabled or not text:
            return

        # Strip markdown syntax and emojis for clean speech
        clean = re.sub(r"[*#_`\[\]\(\)>~]", "", text)
        clean = re.sub(r"[^\x00-\x7F]+", "", clean).strip()
        if not clean:
            return

        def _do_speak():
            with self._speech_lock:
                try:
                    p = subprocess.Popen(
                        [
                            "powershell",
                            "-NoProfile",
                            "-Command",
                            "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak([Console]::In.ReadToEnd())"
                        ],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )
                    p.communicate(input=clean[:250])
                except Exception:
                    pass

        threading.Thread(target=_do_speak, daemon=True).start()

    def listen_for_voice(self, timeout_sec: int = 8) -> Optional[str]:
        """Listens to PC microphone via Windows Native Speech Recognition."""
        print(f"\n{C.YELLOW}{C.BOLD}🎙️ [Microphone Active]{C.RESET} Speak your command clearly into the microphone...")
        ps_cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine; "
            "$r.SetInputToDefaultAudioDevice(); "
            "$grammar = New-Object System.Speech.Recognition.DictationGrammar; "
            "$r.LoadGrammar($grammar); "
            f"$res = $r.Recognize([TimeSpan]::FromSeconds({timeout_sec})); "
            "if ($res) { Write-Output $res.Text } else { Write-Output '' }"
        )
        try:
            p = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=timeout_sec + 5
            )
            heard = p.stdout.strip()
            return heard if heard else None
        except Exception as e:
            print(f"{C.RED}[Voice Input Note] {e}{C.RESET}")
            return None

    def print_banner(self):
        print(f"\n{C.CYAN}{C.BOLD}{'='*75}")
        print("   JARVIS // COGNITIVE MULTI-AGENT OS — TERMINAL INTERFACE")
        print("   Chief Systems Architect: Ansh Tiwari")
        print(f"{'='*75}{C.RESET}")
        print(f"{C.DIM}Voice Output: {C.GREEN}ON{C.RESET}{C.DIM} (type 'voice off' to mute) | Type 'help' for commands | 'exit' to quit{C.RESET}\n")

    def print_help(self):
        print(f"\n{C.BOLD}Available CLI Directives & Commands:{C.RESET}")
        print(f"  {C.CYAN}<any natural directive>{C.RESET}  Deploy autonomous multi-agent swarm (code, SaaS, microservices, business)")
        print(f"  {C.CYAN}listen / mic{C.RESET}             Activate microphone and speak your command using Windows voice recognition")
        print(f"  {C.CYAN}browse <goal or query>{C.RESET}   Autonomous web discovery & DOM interaction (Zero templates; figures out links on its own)")
        print(f"  {C.CYAN}transcript <media_url>{C.RESET}   Extract transcript from video/IG reel via progressive fallback (No official API needed)")
        print(f"  {C.CYAN}outreach <niche> [hook]{C.RESET}  Compile high-efficiency cold outreach system (<30c subject, <100w body, 4-stage follow-up)")
        print(f"  {C.CYAN}chat <message>{C.RESET}           Direct conversational dialogue with Jarvis Central Brain (with voice narration)")
        print(f"  {C.CYAN}browser inbox [idx]{C.RESET}      Open active Gmail inbox (https://mail.google.com/mail/u/0/#inbox) in host browser")
        print(f"  {C.CYAN}browser compose <to> <subj> <body>{C.RESET} Open Gmail Compose tab pre-filled in host browser session")
        print(f"  {C.CYAN}browser open <url>{C.RESET}       Open any URL in user's active host browser")
        print(f"  {C.CYAN}browser run <url>{C.RESET}        Launch Playwright engine with smart locator, scrolling, and gestures")
        print(f"  {C.CYAN}history{C.RESET}                  List recent missions, sessions, and generated deliverables")
        print(f"  {C.CYAN}session <id>{C.RESET}             Inspect artifacts and file deliverables for a past mission")
        print(f"  {C.CYAN}export <id> [path]{C.RESET}       Export deliverables to host Downloads or custom directory")
        print(f"  {C.CYAN}workflows{C.RESET}                View saved recurring workflows")
        print(f"  {C.CYAN}schedules{C.RESET}                View active background cron schedules")
        print(f"  {C.CYAN}voice [on|off]{C.RESET}           Toggle Windows native spoken voice synthesis")
        print(f"  {C.CYAN}clear{C.RESET}                    Clear terminal screen")
        print(f"  {C.CYAN}exit{C.RESET}                     Quit Jarvis CLI\n")

    async def handle_chat(self, message: str):
        from core.config import settings
        low = message.lower().strip()

        # Proactive Auto-Routing: If user passed an actionable directive in chat, route to execution
        if any(w in low for w in ["send mail", "send email", "send 3 mail", "send 3 email", "mails to", "email to"]) or (
            re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', low) and any(act in low for act in ["send", "write", "compose", "dispatch", "mail"])
        ):
            print(f"\n{C.YELLOW}{C.BOLD}[Auto-Route]{C.RESET} Actionable communication directive recognized in chat. Launching autonomous swarm pipeline...")
            await self.run_mission(message)
            return

        # Proactive Auto-Routing: Browser / Media Playback directives in chat
        if any(k in low for k in ["youtube", "karan aujla", "play song", "play the song", "play music", "at peace", "at peach"]) or low.startswith(("browse ", "play ", "open browser ", "search web ")):
            print(f"\n{C.YELLOW}{C.BOLD}[Auto-Route]{C.RESET} Browser media directive recognized in chat. Launching Autonomous Browser Agent...")
            await self.handle_autonomous_browse(message)
            return

        print(f"\n{C.BLUE}{C.BOLD}[Jarvis Brain Thinking...]{C.RESET}")
        try:
            llm = settings.get_llm_client()
            resp = creator_memory.chat_response(
                user_message=message,
                is_mock=settings.is_mock(),
                llm_client=llm
            )
            text = resp.get("text", "")
            print(f"\n{C.GREEN}{C.BOLD}Jarvis:{C.RESET} {text}\n")
            audio_text = resp.get("speech_audio") or text
            if audio_text:
                self.speak(audio_text[:200])
        except Exception as e:
            print(f"{C.RED}[Error] Central Brain communication error: {e}{C.RESET}")

    async def run_mission(self, directive: str):
        """Executes the full 5-stage multi-agent swarm pipeline from the terminal."""
        print(f"\n{C.CYAN}{C.BOLD}[Stage 1/5] Analyzing Directive & Requirements...{C.RESET}")
        self.speak("Directive received. Analyzing architecture and assembling specialized agent army.")

        analysis = orchestrator.analyze_intent(vision=directive)
        session_id = analysis.session_id
        self.active_session_id = session_id

        print(f"  • Mission ID: {C.BOLD}{session_id}{C.RESET}")
        print(f"  • Track Identified: {C.YELLOW}{analysis.track_type}{C.RESET}")
        print(f"  • Swarm Scale: {C.GREEN}{analysis.swarm_size_descriptor}{C.RESET}")

        answers = dict(analysis.recommended_defaults)

        # Clarifying Questions (Interactive)
        if analysis.clarifications:
            print(f"\n{C.YELLOW}{C.BOLD}Foundational Architectural Decisions ({len(analysis.clarifications)} points):{C.RESET}")
            for idx, q in enumerate(analysis.clarifications, 1):
                default_val = q.default_selection or q.options[0]
                print(f"  {idx}. {C.BOLD}{q.question}{C.RESET}")
                print(f"     {C.DIM}{q.why_needed}{C.RESET}")
                print(f"     {C.GREEN}✓ Auto-Selected Optimal Policy: {default_val}{C.RESET}")

        print(f"\n{C.CYAN}{C.BOLD}⚡ Deploying Autonomous Swarm Pipeline (Zero Clicks Required)...{C.RESET}\n")
        self.speak("Commencing dynamic knowledge gathering and runtime DAG compilation.")

        # Event stream handler for live terminal display
        async def cli_event_listener(evt: ExecutionEvent):
            if evt.speech_text:
                self.speak(evt.speech_text)

            if evt.event_type == "stage_change":
                print(f"\n{C.MAGENTA}{C.BOLD}▶ [STAGE {evt.stage}/5] {evt.message}{C.RESET}")
            elif evt.event_type == "kb_updated":
                print(f"  {C.BLUE}[Knowledge Base]{C.RESET} {evt.message}")
            elif evt.event_type == "dag_generated":
                dag_nodes = evt.data.get("dag", {}).get("nodes", []) if evt.data else []
                print(f"  {C.CYAN}[DAG Compiled]{C.RESET} {evt.message} ({len(dag_nodes)} specialized sub-agents)")
                for node in dag_nodes:
                    print(f"    • Agent [{node.get('id')}]: {node.get('description', '')[:70]}")
            elif evt.event_type == "task_start":
                print(f"  {C.YELLOW}⚡ [Agent Active]{C.RESET} {evt.task_id} -> {evt.message}")
            elif evt.event_type == "task_complete":
                print(f"  {C.GREEN}✓ [Agent Complete]{C.RESET} {evt.task_id} -> {evt.message}")
            elif evt.event_type == "self_correction":
                print(f"  {C.RED}⚠ [Self-Correction Triggered]{C.RESET} {evt.message}")
            elif evt.event_type == "evaluation_passed":
                print(f"  {C.GREEN}★ [Quality Gatekeeper Certified]{C.RESET} {evt.message}")
            elif evt.event_type == "done":
                print(f"\n{C.GREEN}{C.BOLD}🎉 [MISSION ACCOMPLISHED & CERTIFIED]{C.RESET} {evt.message}")
                deliverables = evt.data.get("deliverables", []) if evt.data else []
                if deliverables:
                    print(f"\n{C.BOLD}Generated Workspace Deliverables ({len(deliverables)} files):{C.RESET}")
                    for f in deliverables:
                        fname = f if isinstance(f, str) else f.get("path", "")
                        print(f"  {C.CYAN}[File]{C.RESET} workspaces/{session_id}/{fname}")
                self.speak("Mission accomplished, Master Ansh. All tasks verified and deliverables ready.")
            elif evt.event_type == "error":
                print(f"  {C.RED}✖ [Error]{C.RESET} {evt.message}")

        session = orchestrator.get_or_create_session(session_id)

        # Concurrently consume events from session.event_queue
        async def event_consumer():
            while True:
                try:
                    evt: ExecutionEvent = await asyncio.wait_for(session.event_queue.get(), timeout=120)
                    await cli_event_listener(evt)
                    if evt.event_type in ["done", "error"]:
                        break
                except asyncio.TimeoutError:
                    break

        consumer_task = asyncio.create_task(event_consumer())

        # Launch execution
        await orchestrator.execute_full_lifecycle(
            session_id=session_id,
            clarification_answers=answers
        )

        try:
            await asyncio.wait_for(consumer_task, timeout=10)
        except asyncio.TimeoutError:
            pass

    async def handle_autonomous_browse(self, goal_or_query: str):
        """
        Dedicated Autonomous Browser Agent (Interactive Perception-Action Loop).
        Figures out destination links, perceives live DOM interactive elements, and navigates on its own.
        """
        from core.browser_agent import browser_agent
        print(f"\n{C.CYAN}{C.BOLD}[Autonomous Browser Agent]{C.RESET} Exploring objective dynamically...")
        print(f"  • Objective: {C.YELLOW}{goal_or_query}{C.RESET}")
        print(f"  • Policy: {C.GREEN}Perception-Action Loop / Interactive DOM Perception / Zero Templates{C.RESET}")
        self.speak("Commencing autonomous web exploration and live DOM discovery.")

        res = await asyncio.to_thread(
            browser_agent.execute_goal,
            goal=goal_or_query,
            headless=False,
            max_steps=6
        )

        if not res.get("success"):
            print(f"{C.RED}[Error] Browser Agent encountered issue: {res.get('error')}{C.RESET}")
            return

        print(f"\n{C.GREEN}{C.BOLD}✓ Autonomous Browser Agent Completed Objective:{C.RESET}")
        print(f"  • Final Destination: {C.CYAN}{res.get('final_url')}{C.RESET}")
        print(f"  • Page Title: {C.BOLD}{res.get('final_title')}{C.RESET}")
        print(f"  • Summary: {C.GREEN}{res.get('summary')}{C.RESET}")

        logs = res.get("execution_log", [])
        if logs:
            print(f"\n{C.BOLD}Perception & Action Trace ({len(logs)} steps):{C.RESET}")
            for l in logs:
                print(f"  ✓ {l}")

        if res.get("final_screenshot"):
            print(f"\n  • Visual Proof Screenshot: {C.CYAN}{res.get('final_screenshot')}{C.RESET}\n")

        self.speak(f"Browser exploration complete. {res.get('summary', '')[:100]}")

    def handle_transcript_cmd(self, url: str):
        print(f"\n{C.CYAN}{C.BOLD}[Creative Problem Solver]{C.RESET} Analyzing target media without official API: {C.YELLOW}{url}{C.RESET}")
        self.speak("Commencing progressive fallback deduction to extract media transcript.")
        res = CreativeProblemSolver.extract_media_transcript_without_api(url)

        print(f"\n{C.BOLD}Autonomous Deduction Ladder:{C.RESET}")
        for step in res.get("deduction_log", []):
            print(f"  • {C.DIM}{step}{C.RESET}")

        print(f"\n{C.GREEN}{C.BOLD}✓ Extracted Certified Transcript:{C.RESET}\n")
        print(f"{C.CYAN}{res.get('transcript')}{C.RESET}\n")
        self.speak("Transcript successfully extracted and verified.")

    def handle_outreach_cmd(self, niche: str, hook: str):
        print(f"\n{C.CYAN}{C.BOLD}[Strategic Outreach Architect]{C.RESET} Compiling high-efficiency system for: {C.YELLOW}{niche}{C.RESET}")
        self.speak("Compiling cold outreach infrastructure with collision-free port guards.")
        res = StrategicOutreachArchitect.compile_high_efficiency_outreach_suite(target_niche=niche, value_hook=hook)

        print(f"  • Allocated Safe Port: {C.GREEN}{res.get('allocated_port')}{C.RESET} (Collision-Free Guarantee)")
        rules = res.get("rules_enforced", {})
        print(f"  • Deep Domain Rules: Subject < {rules.get('max_subject_length')} chars | Body < {rules.get('max_body_words')} words")
        print(f"  • Strategic Insight: {C.YELLOW}{rules.get('follow_up_ratio')}{C.RESET}")

        print(f"\n{C.BOLD}Compiled 4-Touch Follow-Up Cadence:{C.RESET}")
        for touch in res.get("cadence", []):
            print(f"\n  {C.MAGENTA}[{touch['timing']}]{C.RESET} Subject: '{C.BOLD}{touch['subject']}{C.RESET}' ({touch['body_word_count']} words)")
            print(f"  {C.DIM}{touch['body']}{C.RESET}")

        out_dir = Path("workspaces/outreach_system")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "safe_webhook_receiver.py").write_text(res.get("webhook_receiver_code", ""), encoding="utf-8")
        print(f"\n{C.GREEN}✓ Outreach receiver script generated: {out_dir / 'safe_webhook_receiver.py'}{C.RESET}\n")
        self.speak("Outreach infrastructure compiled. 4-touch follow-up cadence active.")

    async def handle_browser_cmd(self, parts: list[str]):
        """Direct browser automation commands from terminal."""
        if len(parts) < 2:
            print(f"{C.RED}Usage: browser <demo|inbox|compose|open|run|agent|email|login> [arguments]{C.RESET}")
            return

        sub = parts[1].lower()

        if sub == "inbox":
            account_idx = int(parts[2]) if len(parts) > 2 else 0
            url = f"https://mail.google.com/mail/u/{account_idx}/#inbox"
            print(f"{C.CYAN}Opening active host Gmail inbox in your logged-in browser session:{C.RESET} {url}")
            success = BrowserController.open_gmail_inbox(account_idx)
            if success:
                print(f"{C.GREEN}✓ Browser launched directly into primary logged-in Gmail inbox (u/{account_idx}).{C.RESET}")
                self.speak("Opening your live Gmail inbox.")
            else:
                print(f"{C.RED}Failed to launch host browser.{C.RESET}")

        elif sub == "compose":
            if len(parts) < 5:
                print(f"{C.RED}Usage: browser compose <recipient> <subject> <body>{C.RESET}")
                return
            to = parts[2]
            subject = parts[3]
            body = " ".join(parts[4:])
            print(f"{C.CYAN}Opening Gmail Compose for {to} in logged-in user session...{C.RESET}")
            res = BrowserController.compose_in_gmail(recipient=to, subject=subject, body=body)
            if res.get("success"):
                print(f"{C.GREEN}✓ Compose tab opened in your browser with recipient, subject, and body prefilled.{C.RESET}")
                self.speak(f"Composing email to {to}.")
            else:
                print(f"{C.RED}Failed to open compose tab.{C.RESET}")

        elif sub == "open":
            if len(parts) < 3:
                print(f"{C.RED}Usage: browser open <url>{C.RESET}")
                return
            url = parts[2]
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            print(f"{C.CYAN}Opening in host browser:{C.RESET} {url}")
            BrowserController.open_in_system_browser(url)

        elif sub == "run":
            if len(parts) < 3:
                print(f"{C.RED}Usage: browser run <url>{C.RESET}")
                return
            url = parts[2]
            print(f"{C.CYAN}Launching Playwright autonomous engine on:{C.RESET} {url}")
            res = await asyncio.to_thread(
                BrowserController.run_playwright_automation,
                url=url,
                headless=False,
                actions=[
                    {"type": "scroll", "direction": "down", "distance": 300},
                    {"type": "wait", "ms": 1000}
                ],
                screenshot_path="workspaces/screenshots/cli_browser_run.png"
            )
            print(f"{C.GREEN}✓ Browser automation completed:{C.RESET} {res.get('title')}")
            for a in res.get("executed_actions", []):
                print(f"  • {a}")
            if res.get("screenshot"):
                print(f"  • Screenshot saved: {res.get('screenshot')}")

        elif sub == "agent":
            if len(parts) < 3:
                print(f"{C.RED}Usage: browser agent <goal>{C.RESET}")
                return
            goal = " ".join(parts[2:])
            await self.handle_autonomous_browse(goal)

        elif sub == "email":
            if len(parts) < 3:
                print(f"{C.RED}Usage: browser email <recipient> [subject] [body]{C.RESET}")
                return
            to = parts[2]
            subject = parts[3] if len(parts) > 3 else "hello i am jarvis"
            body = " ".join(parts[4:]) if len(parts) > 4 else "I am writing this email as your autonomous technical partner."
            from core.browser_agent import browser_agent
            print(f"{C.CYAN}Dispatching email autonomously to {to}...{C.RESET}")
            res = await asyncio.to_thread(browser_agent.send_email_autonomously, to, subject, body)
            print(f"{C.GREEN}✓ Dispatch Result:{C.RESET} {res.get('message')}")
            for act in res.get("actions", []):
                print(f"  • {act}")
            self.speak(f"Email dispatched for {to}.")

        elif sub in ["login", "auth"]:
            print(f"{C.CYAN}Launching Jarvis Persistent Browser Profile (Axiom Mode)...{C.RESET}")
            print(f"{C.YELLOW}Sign in to your Google Account ONCE in the browser window that appears.\nOnce signed in, Jarvis will autonomously control Gmail, compose, and click Send forever!{C.RESET}")
            self.speak("Launching persistent browser window. Please sign in to your Google account.")
            res = await asyncio.to_thread(BrowserController.launch_login_session)
            if res.get("logged_in"):
                print(f"\n{C.GREEN}{C.BOLD}✓ Authentication session saved! Autonomous browser dispatch is now permanently active.{C.RESET}\n")
                self.speak("Authentication saved. Autonomous dispatch active.")
            else:
                print(f"\n{C.DIM}Session closed. Profile saved at: {res.get('profile_path')}{C.RESET}\n")

        elif sub == "demo":
            print(f"{C.CYAN}Launching live visible desktop browser demonstration on your screen...{C.RESET}")
            self.speak("Launching live visible browser demonstration on your desktop screen.")
            from workspaces.live_browser_demo import run_live_demo
            await asyncio.to_thread(run_live_demo)

        elif sub == "play":
            if len(parts) < 3:
                print(f"{C.RED}Usage: browser play <song or video title>{C.RESET}")
                return
            song = " ".join(parts[2:])
            await self.handle_autonomous_browse(f"go to youtube and play {song}")

    def list_history(self):
        items = workflow_manager.list_history()
        if not items:
            print(f"{C.DIM}No previous mission history found.{C.RESET}")
            return

        print(f"\n{C.BOLD}Recent Missions ({len(items)}):{C.RESET}")
        for it in items[:15]:
            sid = it.get("session_id", "")
            title = it.get("title", "") or it.get("prompt", "")[:45]
            folder = it.get("folder", "General")
            files = len(it.get("deliverables", []) or it.get("artifacts", []))
            print(f"  • [{folder}] {C.CYAN}{sid}{C.RESET}: {title} ({files} files)")
        print()

    def list_workflows(self):
        wfs = workflow_manager.list_workflows()
        if not wfs:
            print(f"{C.DIM}No saved workflows found.{C.RESET}")
            return
        print(f"\n{C.BOLD}Saved Production Workflows ({len(wfs)}):{C.RESET}")
        for w in wfs:
            wid = w.get("id", "")
            title = w.get("title", "")
            folder = w.get("folder", "General")
            desc = w.get("description", "")
            print(f"  • [{folder}] {C.CYAN}{wid}{C.RESET}: {C.BOLD}{title}{C.RESET}")
            print(f"    {C.DIM}{desc}{C.RESET}")
        print()

    def list_schedules(self):
        scheds = workflow_manager.list_schedules()
        if not scheds:
            print(f"{C.DIM}No active scheduled tasks.{C.RESET}")
            return
        print(f"\n{C.BOLD}Active Scheduled Tasks ({len(scheds)}):{C.RESET}")
        for s in scheds:
            sid = s.get("task_id", "")
            name = s.get("name", "")
            cron = s.get("cron", "")
            active = s.get("is_active", True)
            status = f"{C.GREEN}ACTIVE{C.RESET}" if active else f"{C.RED}PAUSED{C.RESET}"
            print(f"  • {C.CYAN}{sid}{C.RESET}: {name} [{status}] ({cron})")
        print()

    def inspect_session(self, session_id: str):
        session_dir = Path("workspaces") / session_id
        if not session_dir.exists():
            print(f"{C.RED}Session '{session_id}' not found in workspaces/.{C.RESET}")
            return

        files = list(session_dir.glob("**/*"))
        files = [f for f in files if f.is_file() and not f.name.endswith(".pyc")]
        print(f"\n{C.BOLD}Workspace for Session:{C.RESET} {C.CYAN}{session_id}{C.RESET}")
        print(f"Path: {session_dir.resolve()}\n")

        for f in files:
            rel = f.relative_to(session_dir)
            size = f.stat().st_size
            print(f"  • {C.GREEN}{rel}{C.RESET} ({size} bytes)")
        print()

    def export_session(self, session_id: str, custom_dest: Optional[str] = None):
        session_dir = Path("workspaces") / session_id
        if not session_dir.exists():
            print(f"{C.RED}Session '{session_id}' not found.{C.RESET}")
            return

        dest = Path(custom_dest) if custom_dest else (Path.home() / "Downloads" / f"jarvis_export_{session_id}")
        dest.mkdir(parents=True, exist_ok=True)

        count = 0
        for f in session_dir.glob("**/*"):
            if f.is_file() and not f.name.endswith(".pyc"):
                rel = f.relative_to(session_dir)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())
                count += 1

        print(f"\n{C.GREEN}✓ Exported {count} deliverable files to:{C.RESET} {dest.resolve()}\n")
        self.speak(f"Exported {count} deliverables to your destination.")

    async def process_directive(self, line: str) -> bool:
        """Processes any typed or spoken directive. Returns False to exit."""
        line = line.strip()
        if not line:
            return True

        low = line.lower()
        if low in ["exit", "quit", "q", "power down", "goodbye"]:
            print(f"\n{C.DIM}Powering down terminal interface. Central Brain standing by.{C.RESET}")
            self.speak("Standing by, Master Ansh.")
            return False

        if low in ["help", "?", "commands"]:
            self.print_help()
            return True

        if low in ["clear", "cls"]:
            os.system("cls" if os.name == "nt" else "clear")
            self.print_banner()
            return True

        if low.startswith("voice "):
            parts = low.split()
            if len(parts) > 1:
                self.voice_enabled = (parts[1] == "on")
                print(f"Voice output set to: {C.GREEN if self.voice_enabled else C.RED}{'ON' if self.voice_enabled else 'OFF'}{C.RESET}\n")
                if self.voice_enabled:
                    self.speak("Voice output activated.")
            return True

        if low in ["listen", "mic", "voice in", "speak"]:
            self.speak("Listening for your voice command.")
            heard = self.listen_for_voice(timeout_sec=8)
            if heard:
                print(f"\n{C.GREEN}{C.BOLD}🎙️ [Heard Command]:{C.RESET} '{heard}'\n")
                return await self.process_directive(heard)
            else:
                print(f"{C.DIM}[No voice command detected or microphone timed out]{C.RESET}\n")
                return True

        if low.startswith("browse "):
            goal = line[7:].strip()
            await self.handle_autonomous_browse(goal)
            return True

        if low.startswith("transcript "):
            url = line[11:].strip()
            self.handle_transcript_cmd(url)
            return True

        if low.startswith("outreach "):
            parts = line[9:].strip().split(maxsplit=1)
            niche = parts[0] if parts else "Distributed Infrastructure"
            hook = parts[1] if len(parts) > 1 else "reduces latency by 60%"
            self.handle_outreach_cmd(niche, hook)
            return True

        if low.startswith("browser "):
            parts = shlex.split(line)
            await self.handle_browser_cmd(parts)
            return True

        if low in ["workflows", "workflow"]:
            self.list_workflows()
            return True

        if low in ["schedules", "schedule"]:
            self.list_schedules()
            return True

        if low == "history":
            self.list_history()
            return True

        if low.startswith("session "):
            parts = line.split()
            if len(parts) > 1:
                self.inspect_session(parts[1])
            return True

        if low.startswith("export "):
            try:
                parts = shlex.split(line)
            except Exception:
                parts = line.split()
            if len(parts) > 1:
                sid = parts[1]
                dest = parts[2] if len(parts) > 2 else None
                self.export_session(sid, dest)
            return True

        if low.startswith("chat "):
            msg = line[5:].strip()
            await self.handle_chat(msg)
            return True

        # Proactive Auto-Routing: Browser / Media Playback / Web directives
        browser_media_keywords = [
            "youtube", "karan aujla", "play song", "play the song", "play music",
            "at peace", "at peach", "on youtube", "watch video", "listen to",
            "wikipedia", "github.com", "ycombinator", "hacker news", "duckduckgo",
            ".com", ".org", ".io", ".net", "http://", "https://"
        ]
        if any(k in low for k in browser_media_keywords) or low.startswith(("play ", "browse ", "goto ", "go to ", "open ", "visit ", "search ")):
            goal = line
            if low.startswith("browse "):
                goal = line[7:].strip()
            print(f"\n{C.YELLOW}{C.BOLD}[Auto-Route]{C.RESET} Browser/Web directive recognized. Launching Autonomous Browser Agent...")
            await self.handle_autonomous_browse(goal)
            return True

        # Autonomous Multi-Agent Swarm execution for actionable directives
        await self.run_mission(line)
        return True

    async def run_interactive(self):
        self.print_banner()
        self.speak("Jarvis Terminal Cognitive Interface online. Standing by for directives, Master Ansh.")

        while True:
            try:
                line = input(f"{C.BOLD}{C.BLUE}Jarvis > {C.RESET}").strip()
                should_continue = await self.process_directive(line)
                if not should_continue:
                    break
            except (KeyboardInterrupt, EOFError):
                print(f"\n{C.DIM}Session interrupted. Central Brain standing by.{C.RESET}")
                break
            except Exception as e:
                print(f"\n{C.RED}[Error] {e}{C.RESET}\n")


def main():
    cli = JarvisCLI()
    asyncio.run(cli.run_interactive())


if __name__ == "__main__":
    main()
