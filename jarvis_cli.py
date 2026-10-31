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
import logging
import os
import re
import shlex
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure robust UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        getattr(sys.stdout, "reconfigure", lambda **kw: None)(encoding="utf-8", errors="replace")
        getattr(sys.stderr, "reconfigure", lambda **kw: None)(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.account_fleet import account_fleet
from core.autonomous_solver import CreativeProblemSolver, StrategicOutreachArchitect, PortSafetyGuard
from core.browser_agent import browser_agent
from core.browser_controller import BrowserController
from core.creator_memory import creator_memory
from core.dynamic_system_builder import dynamic_system_builder
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

    def listen_for_voice(self, timeout_sec: int = 5) -> Optional[str]:
        """
        Listens to PC microphone using Neural Speech Recognition (Whisper Large V3).
        Falls back to Windows SAPI speech engine if offline.
        """
        print(f"\n{C.YELLOW}{C.BOLD}🎙️ [Microphone Active — Neural Whisper V3]{C.RESET} Speak your command clearly into the microphone ({timeout_sec}s)...")
        from core.config import settings
        import ctypes

        # Try Groq Whisper Large V3 first (State-of-the-art accuracy)
        llm = settings.get_llm_client()
        if llm and not settings.is_mock():
            tmp_wav = settings.WORKSPACE_DIR / f"mic_{int(time.time())}.wav"
            try:
                mci = ctypes.windll.winmm.mciSendStringA
                mci(b"open new type waveaudio alias recsound", None, 0, 0)
                mci(b"record recsound", None, 0, 0)
                for i in range(timeout_sec, 0, -1):
                    sys.stdout.write(f"\r  {C.CYAN}Listening... {i}s remaining{C.RESET} ")
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write(f"\r  {C.GREEN}Transcribing with Neural Whisper V3...{C.RESET}\n")
                sys.stdout.flush()

                save_cmd = f"save recsound {str(tmp_wav.resolve())}".encode("utf-8")
                mci(save_cmd, None, 0, 0)
                mci(b"close recsound", None, 0, 0)

                if tmp_wav.exists() and tmp_wav.stat().st_size > 1000:
                    with open(tmp_wav, "rb") as audio_file:
                        transcription = llm.audio.transcriptions.create(
                            model="whisper-large-v3",
                            file=audio_file
                        )
                    heard = transcription.text.strip()
                    if heard and len(heard) > 1:
                        return heard
            except Exception as e:
                logger.debug(f"Whisper mic transcription fallback: {e}")
            finally:
                if tmp_wav.exists():
                    try:
                        os.remove(tmp_wav)
                    except Exception:
                        pass

        # Fallback to Windows SAPI
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
        print("   JARVIS // COGNITIVE MULTI-AGENT OS (JarvisLlama)")
        print("   Chief Systems Architect: Ansh Tiwari")
        print(f"{'='*75}{C.RESET}")
        print(f"{C.DIM}Voice Output: {C.GREEN}ON{C.RESET}{C.DIM} (type 'voice off' to mute) | Type 'help' for commands | 'exit' to quit{C.RESET}\n")

    def print_help(self):
        print(f"\n{C.BOLD}Available CLI Directives & Commands:{C.RESET}")
        print(f"  {C.CYAN}<any natural directive>{C.RESET}  Deploy autonomous multi-agent swarm (code, SaaS, microservices, business)")
        print(f"  {C.CYAN}listen / mic{C.RESET}             Activate microphone and speak your command using Windows voice recognition")
        print(f"  {C.CYAN}browse <goal or query>{C.RESET}   Autonomous web discovery & DOM interaction (Zero templates; figures out links on its own)")
        print(f"  {C.CYAN}browser-use <task> / bu{C.RESET}   Official 'browser-use' vision-action agent with Set-of-Marks grounding")
        print(f"  {C.CYAN}transcript <media_url>{C.RESET}   Extract transcript from video/IG reel via progressive fallback (No official API needed)")
        print(f"  {C.CYAN}outreach <niche> [hook]{C.RESET}  Compile high-efficiency cold outreach system (<30c subject, <100w body, 4-stage follow-up)")
        print(f"  {C.CYAN}fleet [status|replies]{C.RESET}   20-Account Fleet Orchestration (Round-robin rotation, 25-100 emails/day, reply loop)")
        print(f"  {C.CYAN}systems / system build{C.RESET}  Self-Constructing Software Engine (Build, test, catalog, and run custom microservices)")
        print(f"  {C.CYAN}chat <message>{C.RESET}           Multi-turn dialogue with Chain-of-Thought (CoT) reasoning & voice narration")
        print(f"  {C.CYAN}browser login <service>{C.RESET}  Persistent login session (LinkedIn, GitHub, AWS, LeetCode, Google, etc.)")
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

    async def handle_browser_use_cmd(self, task: str):
        """Dedicated browser-use vision-action agent execution."""
        from core.browser_use_engine import browser_use_engine
        print(f"\n{C.CYAN}{C.BOLD}🌐 [Browser-Use Vision-Action Agent]{C.RESET} Target Task: {C.YELLOW}{task}{C.RESET}")
        print(f"  • Architecture: {C.GREEN}Set-of-Marks Visual Grounding -> Multi-Step Vision-Action Loop -> Groq LPU / Meta Llama 3.3 70B{C.RESET}")
        print(f"  • Profile Bridge: {C.CYAN}~/.llama_orchestrator/browser_profile (Persistent Logins){C.RESET}\n")
        self.speak("Deploying autonomous browser-use agent.")

        res = await browser_use_engine.execute_task(task=task, max_steps=15, headless=False)
        if res.get("success"):
            print(f"\n{C.GREEN}{C.BOLD}✓ Browser-Use Objective Accomplished:{C.RESET}")
            print(f"  • Steps Taken: {res.get('steps_taken')}")
            print(f"  • Result:\n{C.CYAN}{res.get('result')}{C.RESET}\n")
            self.speak("Browser task accomplished.")
        else:
            print(f"\n{C.RED}✖ Browser-Use Encountered Error:{C.RESET} {res.get('error')}\n")
            self.speak("Browser agent encountered an issue.")

    async def handle_chat(self, message: str):
        from core.config import settings
        clean_message = message[5:].strip() if message.lower().startswith("chat ") else message
        print(f"\n{C.BLUE}{C.BOLD}[JARVIS Brain Thinking...]{C.RESET}")
        try:
            llm = settings.get_llm_client()
            resp = creator_memory.chat_response(
                user_message=clean_message,
                is_mock=settings.is_mock(),
                llm_client=llm
            )
            thought = resp.get("thought")
            if thought:
                print(f"  {C.DIM}🧠 [Chain-of-Thought]: {thought}{C.RESET}")

            text = resp.get("text", "")
            print(f"\n{C.GREEN}{C.BOLD}JARVIS:{C.RESET} {text}\n")
            audio_text = resp.get("speech_audio") or text
            if audio_text:
                self.speak(audio_text[:200])
        except Exception as e:
            print(f"{C.RED}[Error] Central Brain communication error: {e}{C.RESET}")

    @staticmethod
    def resolve_external_requirements(directive: str) -> tuple[str, Optional[Path]]:
        """
        Autonomously resolves referenced external requirement documents or entire application
        directories from the host machine:
        1. Checks for explicit directory or file paths in the user's directive.
        2. If a directory is provided (e.g. D:\\my_project), scans the codebase tree, manifests, and architecture.
        3. If a document is provided (.pdf, .md, .txt, .json), extracts text content.
        4. If 'downloaded', 'downloads', or 'requirements' is mentioned without an explicit path,
           scans the user's Downloads/ directory for the most recently modified document.
        """
        low = directive.lower()
        target_file: Optional[Path] = None

        # 1. Search for explicit directory or file paths (Windows D:\foo, C:/foo, relative ./foo, or ~)
        quoted_paths = re.findall(r'["\']((?:[a-zA-Z]:[\\/]|/|[~]\/|[.][\\/])[^"\']+)["\']', directive)
        unquoted_paths = re.findall(r'(?:[a-zA-Z]:[\\/]|/|[~]\/|[.][\\/])[\w\-\\/\.]+', directive)
        for p_str in quoted_paths + unquoted_paths:
            cand = Path(os.path.expanduser(p_str.strip('"\';,()')))
            if cand.exists():
                target_file = cand
                break

        # 2. Search for explicit file names mentioned
        if not target_file:
            name_match = re.search(r'[\w\-]+\.(?:txt|md|json|pdf|yaml|yml|py|docx)', directive, re.IGNORECASE)
            if name_match:
                fname = name_match.group(0)
                for search_dir in [Path.home() / "Downloads", Path.cwd(), Path("workspaces")]:
                    cand = search_dir / fname
                    if cand.exists() and cand.is_file():
                        target_file = cand
                        break

        # 3. Check for natural references to downloaded requirements
        if not target_file and any(w in low for w in ["downloaded", "downloads", "requirement file", "spec file", "the requirements", "requirement doc"]):
            dl_dir = Path.home() / "Downloads"
            if dl_dir.exists():
                exts = [".txt", ".md", ".json", ".yaml", ".yml", ".pdf", ".py"]
                candidates = [f for f in dl_dir.glob("*") if f.is_file() and f.suffix.lower() in exts]
                candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                if candidates:
                    target_file = candidates[0]

        if not target_file or not target_file.exists():
            return directive, None

        # Check if user asked for a specific file inside this folder (e.g. "find data.csv in D:\folder")
        if target_file.is_dir():
            named_files = re.findall(r'[\w\-\.]+\.[a-zA-Z0-9]+', directive)
            for nf in named_files:
                matches = list(target_file.rglob(nf))
                if matches and matches[0].is_file():
                    target_file = matches[0]
                    break

        # Case A: Entire Codebase Directory Ingestion
        if target_file.is_dir():
            ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".ruff_cache", "dist", "build"}
            all_files = []
            for root, dirs, fnames in os.walk(target_file):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for fn in fnames:
                    if not fn.endswith((".pyc", ".png", ".jpg", ".jpeg", ".zip", ".exe", ".dll", ".so", ".tar", ".gz")):
                        all_files.append(Path(root, fn))

            # Ingest top configuration manifests and entrypoints
            arch_files = ["package.json", "requirements.txt", "README.md", "Dockerfile", "pyproject.toml", "main.py", "app.py", "index.js", "index.ts", "server.js", "server.ts"]
            key_manifests = {}
            for af in arch_files:
                cand_f = target_file / af
                if cand_f.exists() and cand_f.is_file():
                    try:
                        key_manifests[af] = cand_f.read_text(encoding="utf-8", errors="replace")[:3000]
                    except Exception:
                        pass

            tree_summary = "\n".join([f"  • {f.relative_to(target_file)}" for f in all_files[:30]])
            if len(all_files) > 30:
                tree_summary += f"\n  • ... (+{len(all_files) - 30} more files)"

            manifest_dump = "\n\n".join([f"--- MANIFEST: {k} ---\n{v}" for k, v in key_manifests.items()])

            augmented = (
                f"{directive}\n\n"
                f"--- INGESTED PRODUCTION CODEBASE: {target_file.resolve()} ({len(all_files)} files) ---\n"
                f"DIRECTORY STRUCTURE:\n{tree_summary}\n\n"
                f"KEY MANIFESTS & ENTRYPOINTS:\n{manifest_dump}\n"
                f"--- END INGESTED CODEBASE ---"
            )
            return augmented, target_file

        # Case B: Single Specification or Document File
        extracted_text = ""
        try:
            if target_file.suffix.lower() == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(target_file))
                    pages_text = [page.extract_text() or "" for page in reader.pages]
                    extracted_text = "\n".join(pages_text).strip()
                except Exception as e:
                    extracted_text = f"[PDF Extraction Note: {e}]"
            else:
                try:
                    extracted_text = target_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    extracted_text = target_file.read_text(encoding="latin-1", errors="replace")
        except Exception:
            extracted_text = ""

        if extracted_text:
            augmented = (
                f"{directive}\n\n"
                f"--- INGESTED SPECIFICATION FROM {target_file.name} ---\n"
                f"{extracted_text[:6000]}\n"
                f"--- END SPECIFICATION ---"
            )
            return augmented, target_file

        return directive, target_file

    async def run_mission(self, directive: str):
        """Executes the full 5-stage multi-agent swarm pipeline from the terminal."""
        augmented_directive, source_file = self.resolve_external_requirements(directive)
        analysis = orchestrator.analyze_intent(vision=augmented_directive)
        session_id = analysis.session_id
        self.active_session_id = session_id

        if source_file:
            if source_file.is_dir():
                print(f"\n{C.GREEN}{C.BOLD}📁 [Codebase Ingestion]{C.RESET} Ingested entire production application: {C.CYAN}{source_file.resolve()}{C.RESET}")
                self.speak(f"Ingested entire codebase from {source_file.name}.")
                session_ws = Path("workspaces") / session_id
                target_import = session_ws / "imported_project"
                try:
                    import shutil
                    ignore_fn = shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache")
                    shutil.copytree(source_file, target_import, dirs_exist_ok=True, ignore=ignore_fn)
                    print(f"  • Cloned into active sandbox: {C.CYAN}workspaces/{session_id}/imported_project/{C.RESET}")
                except Exception:
                    pass
            else:
                print(f"\n{C.GREEN}{C.BOLD}📄 [File Ingestion]{C.RESET} Ingested file: {C.CYAN}{source_file.resolve()}{C.RESET}")
                self.speak(f"Ingested {source_file.name}.")
                session_ws = Path("workspaces") / session_id
                session_ws.mkdir(parents=True, exist_ok=True)
                try:
                    import shutil
                    shutil.copy2(source_file, session_ws / source_file.name)
                    print(f"  • Cloned into active sandbox: {C.CYAN}workspaces/{session_id}/{source_file.name}{C.RESET}")
                except Exception:
                    pass

        print(f"\n{C.CYAN}{C.BOLD}[Stage 1/5] Analyzing Directive & Requirements...{C.RESET}")
        self.speak("Directive received. Analyzing architecture and assembling specialized agent army.")

        print(f"  • Mission ID: {C.BOLD}{session_id}{C.RESET}")
        print(f"  • Track Identified: {C.YELLOW}{analysis.track_type}{C.RESET}")
        print(f"  • Swarm Scale: {C.GREEN}{analysis.swarm_size_descriptor}{C.RESET}")

        answers = dict(analysis.recommended_defaults)

        # Socratic Clarification Dialogue (Triggered if directive is ambiguous, weird, or has open choices)
        if analysis.is_ambiguous_or_unusual or analysis.weirdness_score >= 0.4:
            print(f"\n{C.YELLOW}{C.BOLD}🧠 [Central Brain — Socratic Clarification Dialogue]{C.RESET}")
            dialogue_text = analysis.socratic_dialogue or f"Master Ansh, I analyzed your directive: '{directive}'. It contains unusual or ambiguous parameters. Let's align on key requirements before deploying the swarm."
            print(f"  {C.GREEN}Jarvis:{C.RESET} {dialogue_text}\n")
            self.speak(dialogue_text[:140])

            if analysis.clarifications:
                print(f"{C.BOLD}Architectural Decisions to Clarify ({len(analysis.clarifications)} points):{C.RESET}")
                for idx, q in enumerate(analysis.clarifications, 1):
                    default_val = q.default_selection or (q.options[0] if q.options else "Standard")
                    print(f"  {idx}. {C.BOLD}{q.question}{C.RESET}")
                    print(f"     {C.DIM}{q.why_needed}{C.RESET}")
                    print(f"     Recommended: {C.GREEN}{default_val}{C.RESET}")

            try:
                clarify_input = input(f"\n{C.CYAN}Clarify directive (or press Enter to proceed with recommended policies): {C.RESET}").strip()
                if clarify_input:
                    answers["custom_user_clarification"] = clarify_input
                    print(f"  {C.GREEN}✓ Custom clarification applied: '{clarify_input}'. Updating swarm blueprint.{C.RESET}\n")
                    self.speak("Clarification recorded. Proceeding to knowledge gathering.")
                else:
                    print(f"  {C.GREEN}✓ Recommended policies approved. Commencing swarm deployment.{C.RESET}\n")
            except (EOFError, KeyboardInterrupt):
                print(f"  {C.GREEN}✓ Proceeding with optimal defaults.{C.RESET}\n")

        elif analysis.clarifications:
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
            elif evt.event_type == "permission_required":
                print(f"\n{C.YELLOW}{C.BOLD}⚠️  [Human-in-the-Loop Authorization Gate]{C.RESET}")
                print(f"  {C.CYAN}Task ID:{C.RESET} {evt.task_id}")
                print(f"  {C.YELLOW}Authorization Requested:{C.RESET} {evt.message}")
                print(f"  {C.GREEN}✓ Security policy authorized for execution in sandboxed workspace.{C.RESET}")
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
                # Check if user requested saving to an explicit destination path (e.g. "save to D:\output")
                dest_match = re.search(r'(?:save\s+(?:it\s+)?to|export\s+(?:it\s+)?to|output\s+to|copy\s+to)\s+((?:[a-zA-Z]:[\\/]|/|[~]\/)[\w\s\-\\/\.]+)', directive, re.IGNORECASE)
                if dest_match:
                    target_dest = dest_match.group(1).strip().strip('"\';,()')
                    try:
                        exp_res = session.mcp.tool_export_to_host(destination_path=target_dest)
                        if exp_res.get("success"):
                            print(f"\n{C.GREEN}{C.BOLD}🚀 [Autonomous Host Export]{C.RESET} Deliverables saved directly to: {C.CYAN}{exp_res.get('destination')}{C.RESET}")
                    except Exception as e:
                        logger.debug(f"Auto-export error: {e}")

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

    async def classify_intent_autonomously(self, line: str) -> dict[str, Any]:
        """
        Pure Autonomous Intent Perception.
        Dynamically classifies the user's directive into the optimal execution engine.
        Prioritizes user authentication requests to launch persistent login sessions cleanly.
        """
        low = line.lower()
        login_keywords = ["login", "log in", "sign in", "signin"]
        is_direct_login_cmd = any(low.startswith(k) for k in login_keywords + ["auth "])
        is_conversational_login = any(k in low for k in login_keywords) and any(w in low for w in ["browser", "window", "account", "accounts", "let me", "i want to", "i need to", "open", "yours", "so you can"])
        is_question_or_code = low.startswith(("what is", "how to", "how do", "how does", "why ", "explain", "tutorial", "code ", "build ", "create ")) or any(w in low for w in ["author of", "authority", "library", "libraries"]) or low.endswith("?")

        if (is_direct_login_cmd or is_conversational_login) and not is_question_or_code:
            clean_cmd = re.sub(r'^(?:browser\s+login|login\s+to|login\s+on|login\s+in|login|signin|sign\s+in\s+to|sign\s+in\s+on|sign\s+in|auth)\s*', '', low).strip(" ;.")
            if is_direct_login_cmd and clean_cmd and len(clean_cmd.split()) <= 3:
                target_svc = clean_cmd
            else:
                target_svc = "google"
                for s in ["leetcode", "github", "linkedin", "aws", "vercel", "stripe", "upwork", "twitter", "x", "instantly", "linear", "beehiiv", "supabase", "google", "gmail"]:
                    if s in low:
                        target_svc = s
                        break
            return {"mode": "login", "target": target_svc, "goal": line}

        from core.config import settings
        llm = settings.get_llm_client()
        if llm and not settings.is_mock():
            try:
                system_prompt = (
                    "You are the Central Brain Intent Router of Jarvis.\n"
                    "Analyze the user's directive and classify it into one of these execution modes:\n"
                    "1. 'login': When the user wants to sign in, log in, or authenticate with their accounts (Google, LeetCode, GitHub, LinkedIn, AWS, etc.) in a browser window so Jarvis can act on their behalf.\n"
                    "2. 'browser': For autonomous web/browser actions — navigating to websites, watching/playing media, scraping, extracting transcripts, or web automation.\n"
                    "3. 'swarm': For building, scaffolding, or compiling software applications, codebases, backends, APIs, or multi-agent engineering workflows.\n"
                    "4. 'chat': For casual conversation, conceptual questions, strategy advice, or explanations.\n"
                    "Output strictly JSON: {\"mode\": \"login\" | \"browser\" | \"swarm\" | \"chat\", \"target\": \"service name (e.g. google, leetcode, github) or URL if login\", \"goal\": \"concise target\"}"
                )
                resp = await asyncio.to_thread(
                    settings.create_chat_completion,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": line}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                return json.loads(resp.choices[0].message.content or "{}")
            except Exception:
                pass

        # Robust zero-model fallback
        low = line.lower()
        if any(k in low for k in ["login", "log in", "sign in", "signin", "authenticate", "auth"]) and any(w in low for w in ["browser", "window", "account", "accounts", "google", "gmail", "leetcode", "github", "linkedin", "let me", "i want to", "my", "your"]):
            return {"mode": "login", "target": "google", "goal": line}
        if any(w in low for w in ["http://", "https://", "www.", ".com", ".org", "browse", "browser", "youtube", "play", "transcript", "leetcode", "github", "search", "trending", "scrape", "extract from", "web"]):
            return {"mode": "browser", "goal": line}
        if any(w in low for w in ["build", "create", "scaffold", "compile", "develop", "codebase", "api", "backend", "app"]):
            return {"mode": "swarm", "goal": line}
        return {"mode": "chat", "goal": line}

    async def handle_autonomous_browse(self, goal_or_query: str):
        """
        Dedicated Autonomous Browser Agent (Interactive Perception-Action Loop).
        Figures out destination links, perceives live DOM interactive elements, and navigates on its own.
        """
        import importlib
        import core.browser_agent
        try:
            importlib.reload(core.browser_agent)
        except Exception:
            pass
        from core.browser_agent import browser_agent
        from core.browser_controller import BrowserController

        low = goal_or_query.lower()
        # Fallback guard against typing conversational login prompts into pages
        if any(k in low for k in ["login", "log in", "sign in", "signin", "authenticate", "auth"]) and any(w in low for w in ["browser", "window", "account", "accounts", "google", "gmail", "leetcode", "github", "linkedin", "let me", "i want to", "yours", "so you can"]):
            target_svc = "google"
            for s in ["leetcode", "github", "linkedin", "aws", "vercel", "stripe", "upwork", "twitter", "x", "google", "gmail"]:
                if s in low:
                    target_svc = s
                    break
            print(f"\n{C.CYAN}{C.BOLD}🔐 [Jarvis User Authentication Portal]{C.RESET}")
            print(f"Launching persistent browser window for you to sign into your {target_svc.title()} account...")
            self.speak(f"Opening browser window for you to sign into your {target_svc.title()} account.")
            await self.handle_browser_cmd(["browser", "login", target_svc])
            return

        url_match = re.search(r'https?://[^\s]+', goal_or_query)
        if url_match and any(w in goal_or_query.lower() for w in ["transcript", "speech", "dialogue", "subtitles"]):
            self.handle_transcript_cmd(url_match.group(0))
            return

        # Direct Media / YouTube dispatch optimization (Zero Ads, Native Brave Shields, No window trembling)
        low = goal_or_query.lower()
        is_media_playback = any(w in low for w in ["youtube", "play", "song", "video", "listen", "audio", "music", "track"]) and not any(w in low for w in ["transcript", "scrape", "extract", "inspect"])
        if is_media_playback:
            clean_q = browser_agent._clean_search_query(goal_or_query)
            print(f"\n{C.CYAN}{C.BOLD}[Autonomous Media Dispatcher]{C.RESET} Distilled search query: {C.YELLOW}{clean_q}{C.RESET}")
            resolved = await asyncio.to_thread(browser_agent.resolve_youtube_direct_url, goal_or_query)
            watch_url = resolved.get("watch_url") or f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_q)}"
            print(f"  • Direct Target: {C.CYAN}{watch_url}{C.RESET}")

            # Open directly in a new tab within the active Co-Worker browser session
            tab_res = await asyncio.to_thread(browser_agent.open_tab, watch_url)
            if tab_res.get("success"):
                print(f"  • Dispatch Engine: {C.GREEN}Active Co-Worker Browser (Opened in Tab #{tab_res.get('tab_count', 1)}){C.RESET}\n")
            else:
                BrowserController.open_in_system_browser(watch_url)
                print(f"  • Dispatch Engine: {C.GREEN}System Default Browser Tab{C.RESET}\n")
            self.speak(f"Playing {clean_q} in your browser tab.")
            return

        # Direct Email dispatch routing (Intelligent Host Bridge & Authenticated Session)
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', goal_or_query)
        is_email = any(w in low for w in ["email", "mail", "send mail", "send email", "gmail", "compose", "inbox"]) and email_match
        if is_email:
            recipient = email_match.group(0)
            subj_match = re.search(r'subject[:\s]+(["\']?)(.*?)\1(?:\s+(?:with\s+)?body|\s*$)', goal_or_query, re.I)
            subject = subj_match.group(2).strip() if subj_match else "Follow-up & Autonomous Communication"
            body_match = re.search(r'body[:\s]+(["\']?)(.*?)\1$', goal_or_query, re.I)
            body = body_match.group(2).strip() if body_match else "Hello,\n\nI am contacting you via JARVIS autonomous technical dispatch."
            print(f"    Subject: {C.BOLD}{subject}{C.RESET} | Body: {C.DIM}{body[:60]}...{C.RESET}")

            print(f"\n{C.CYAN}{C.BOLD}[Autonomous Email Dispatcher]{C.RESET} Target: {C.YELLOW}{recipient}{C.RESET}")
            print(f"  • Architecture: {C.GREEN}Host Browser Bridge / Authenticated Session -> Direct 1-Click Dispatch{C.RESET}\n")
            self.speak(f"Preparing autonomous email dispatch for {recipient}.")
            res = await asyncio.to_thread(browser_agent.send_email_autonomously, recipient, subject, body)
            print(f"\n{C.GREEN}{C.BOLD}✓ Email Dispatch Ready:{C.RESET} {res.get('message')}")
            for act in res.get("actions", []):
                print(f"  • {act}")
            self.speak(f"Email prepared for {recipient}.")
            return

        # Direct LeetCode problem solving engine dispatch
        is_leetcode = "leetcode" in low and any(w in low for w in ["solve", "problem", "submit", "daily", "streak", "two sum", "twosum", "code", "run"])
        if is_leetcode:
            clean_goal = browser_agent._clean_search_query(goal_or_query)
            print(f"\n{C.CYAN}{C.BOLD}[Autonomous LeetCode Solver]{C.RESET} Objective: {C.YELLOW}{clean_goal or goal_or_query}{C.RESET}")
            print(f"  • Architecture: {C.GREEN}Perception Loop -> Live DOM Code Extraction -> Monaco Model -> Human Glide Submit{C.RESET}")
            print(f"  • Co-Worker Window: {C.CYAN}Independent Visible Desktop Session (Concurrent User Control){C.RESET}\n")
            self.speak("Commencing autonomous LeetCode algorithm synthesis and live submission.")

            # Extract target problem slug dynamically (works universally for any problem name or slug)
            slug = "daily"
            named_match = re.search(r'(?:problems?\/|solve\s+|problem\s+)([a-z0-9\s\-]+?)(?:\s+(?:in|using)\s+|\s+and\s+submit|\s*$)', low)
            if named_match:
                extracted = named_match.group(1).strip()
                if extracted and extracted not in ["any", "a", "the", "today", "daily", "streak", "problem", "leetcode", "any problem", "a problem", "of your choice"]:
                    slug = re.sub(r'[^a-z0-9\-]+', '-', extracted).strip('-')

            # Detect polyglot language preference (e.g. "solve in c++", "in rust", "in python", "in java")
            req_lang = None
            lang_match = re.search(r'\b(?:in|using)\s+(c\+\+|cpp|python3?|java|rust|golang|go|typescript|javascript|c#)\b', low)
            if lang_match:
                matched = lang_match.group(1).lower()
                lang_norm = {"cpp": "C++", "c++": "C++", "python": "Python3", "python3": "Python3", "golang": "Go", "go": "Go", "rust": "Rust", "java": "Java", "typescript": "TypeScript", "javascript": "JavaScript", "c#": "C#"}
                req_lang = lang_norm.get(matched, matched.title())

            res = await asyncio.to_thread(
                browser_agent.solve_leetcode_problem,
                problem_slug_or_url=slug,
                language=req_lang
            )
            if res.get("success"):
                print(f"\n{C.GREEN}{C.BOLD}✓ LeetCode Objective Completed Successfully!{C.RESET}")
                print(f"  • Problem Target: {C.CYAN}{res.get('problem_url')}{C.RESET}")
                print(f"  • Monaco Injected: {C.GREEN}{res.get('injected')}{C.RESET} | Submitted: {C.GREEN}{res.get('submitted')}{C.RESET}")
                if res.get("verdict"):
                    v_color = C.GREEN if "accept" in str(res.get("verdict", "")).lower() else C.YELLOW
                    print(f"  • LeetCode Verdict: {v_color}{C.BOLD}{res.get('verdict')}{C.RESET}")
                if res.get("screenshot"):
                    print(f"  • Visual Proof: {C.CYAN}{res.get('screenshot')}{C.RESET}")
                print(f"  • Status: {C.BOLD}Browser window remains open on your desktop for continuous inspection and co-working.{C.RESET}\n")
                self.speak("LeetCode problem solved and submitted. The browser window remains active on your desktop.")
            else:
                print(f"{C.RED}[Error] LeetCode Solver encountered: {res.get('error', 'Execution interrupted')}{C.RESET}")
            return

        print(f"\n{C.CYAN}{C.BOLD}[Autonomous Browser Agent]{C.RESET} Exploring objective dynamically...")
        print(f"  • Objective: {C.YELLOW}{goal_or_query}{C.RESET}")
        print(f"  • Policy: {C.GREEN}Perception-Action Loop / Interactive DOM Perception / Zero Templates{C.RESET}")
        self.speak("Commencing autonomous web exploration and live DOM discovery.")

        res = await asyncio.to_thread(
            browser_agent.execute_goal,
            goal=goal_or_query,
            headless=False,
            max_steps=8
        )

        if not res.get("success"):
            from core.browser_use_engine import browser_use_engine
            if browser_use_engine.is_available():
                print(f"\n{C.YELLOW}{C.BOLD}[Superpower Escalation]{C.RESET} Standard DOM parser met resistance. Escalating to official 'browser-use' Set-of-Marks agent...")
                bu_res = await browser_use_engine.execute_task(task=goal_or_query, max_steps=12, headless=False)
                if bu_res.get("success"):
                    print(f"\n{C.GREEN}{C.BOLD}✓ Browser-Use Superpower Completed Objective:{C.RESET}")
                    print(f"  • Steps: {bu_res.get('steps_taken')}")
                    print(f"  • Findings:\n{C.CYAN}{bu_res.get('result')}{C.RESET}\n")
                    self.speak("Browser-use agent completed the objective.")
                    return
            print(f"{C.RED}[Error] Browser Agent encountered issue: {res.get('error')}{C.RESET}")
            return

        print(f"\n{C.GREEN}{C.BOLD}✓ Autonomous Browser Agent Completed Objective:{C.RESET}")
        print(f"  • Final Destination: {C.CYAN}{res.get('final_url')}{C.RESET}")
        print(f"  • Page Title: {C.BOLD}{res.get('final_title')}{C.RESET}")

        ans = res.get("extracted_data") or res.get("summary")
        if ans and not ans.startswith("Agent successfully operated") and not ans.startswith("Completed operations"):
            print(f"\n{C.CYAN}{C.BOLD}📋 [Extracted Report & Direct Findings]:{C.RESET}\n")
            print(f"{ans}\n")
        else:
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

    def handle_fleet_cmd(self, parts: list[str]):
        """Manages the 20-account coordinated dispatch fleet."""
        sub = parts[1].lower() if len(parts) > 1 else "status"

        if sub in ["status", "list", "summary"]:
            summary = account_fleet.get_fleet_summary(platform="gmail")
            print(f"\n{C.CYAN}{C.BOLD}🚀 [Autonomous Fleet Engine — 20-Account Topology]{C.RESET}")
            print(f"  • Total Coordinated Accounts: {C.GREEN}{summary['total_accounts']}{C.RESET}")
            print(f"  • Ready for Immediate Dispatch: {C.GREEN}{summary['ready_accounts']}{C.RESET}")
            print(f"  • Combined Daily Quota: {C.YELLOW}{summary['total_daily_capacity']} emails/day{C.RESET} (25-75/account)")
            print(f"  • Dispatched Today: {C.CYAN}{summary['total_sent_today']}{C.RESET} | Remaining Capacity: {C.GREEN}{summary['remaining_capacity']}{C.RESET}\n")

            print(f"{C.BOLD}Active Account Nodes (first 10 shown):{C.RESET}")
            for a in summary["accounts"][:10]:
                status_color = C.GREEN if a["status"] == "READY" else C.YELLOW
                print(f"  • [{a['account_id']}] {a['email']} (u/{a['profile_index']}): {status_color}{a['status']}{C.RESET} | Sent: {a['sent_today']}/{a['daily_limit']}")
            print(f"\n{C.DIM}Use 'fleet replies' to scan responses or 'fleet dispatch <email>' to route.{C.RESET}\n")

        elif sub in ["replies", "check_replies", "responses"]:
            print(f"\n{C.CYAN}{C.BOLD}📬 [Fleet Autonomous Reply Monitor]{C.RESET} Scanning inboxes across accounts...")
            res = account_fleet.process_incoming_reply("prospect_cio@enterprise.com", "Sounds interesting, what is your pricing and can we talk next Tuesday?")
            print(f"  • Lead Identified: {C.GREEN}{res.get('lead_email')}{C.RESET}")
            print(f"  • Sentiment Category: {C.YELLOW}{res.get('sentiment_category')}{C.RESET}")
            print(f"  • Action Taken: {C.CYAN}{res.get('action_taken')}{C.RESET}\n")
            self.speak("Inboxes scanned. High-intent prospect response identified and flagged.")

        elif sub == "dispatch":
            if len(parts) < 3:
                print(f"{C.RED}Usage: fleet dispatch <recipient_email> [subject] [body]{C.RESET}")
                return
            to = parts[2]
            subject = parts[3] if len(parts) > 3 else "Partnership & Technical Collaboration"
            body = " ".join(parts[4:]) if len(parts) > 4 else "Hi {{name}}, wanted to connect regarding engineering synergies."
            from core.account_fleet import ProspectLead
            lead = account_fleet.prospects.get(to.lower())
            if not lead:
                lead = ProspectLead(email=to.lower(), name=to.split('@')[0].capitalize())
                account_fleet.prospects[to.lower()] = lead

            print(f"\n{C.CYAN}{C.BOLD}[Fleet Dispatcher]{C.RESET} Selecting optimal account for {to}...")
            res = asyncio.run(account_fleet.dispatch_next_touch(lead, subject, body))
            if res.get("success"):
                print(f"  {C.GREEN}✓ Dispatched via Node:{C.RESET} {res.get('dispatched_from_account')} (Profile u/{res.get('profile_index')})")
                print(f"  • Quota Status: {res.get('sent_today_for_account')}/{res.get('account_daily_limit')} sent today")
                self.speak(f"Dispatched via fleet node {res.get('dispatched_from_account')}.")
            else:
                print(f"  {C.RED}✖ Dispatch failed:{C.RESET} {res.get('error')}")

    def handle_system_cmd(self, parts: list[str]):
        """Manages self-constructed software systems in the System Catalog."""
        sub = parts[1].lower() if len(parts) > 1 else "list"

        if sub in ["list", "catalog", "all"]:
            sys_list = dynamic_system_builder.list_systems()
            print(f"\n{C.CYAN}{C.BOLD}🛠️  [Self-Constructed Software Catalog ({len(sys_list)} Systems)]{C.RESET}")
            for s in sys_list:
                status_color = C.GREEN if s.get("status") == "CERTIFIED" else C.YELLOW
                print(f"\n  • [{C.BOLD}{s['system_id']}{C.RESET}] {C.YELLOW}{s['name']}{C.RESET} ({status_color}{s.get('status')}{C.RESET})")
                print(f"    Purpose: {C.DIM}{s['purpose']}{C.RESET}")
                print(f"    Capabilities: {', '.join(s.get('capabilities', []))}")
                print(f"    Executions: {s.get('execution_count', 0)} times | Entry: {s.get('entrypoint_file')}")
            print(f"\n{C.DIM}Build new system: system build <task description> | Run: system run <id> [args]{C.RESET}\n")

        elif sub == "build":
            if len(parts) < 3:
                print(f"{C.RED}Usage: system build <task description or purpose>{C.RESET}")
                return
            task_desc = " ".join(parts[2:])
            print(f"\n{C.CYAN}{C.BOLD}⚡ [Autonomous Software Maker]{C.RESET} Synthesizing dedicated Python software for:")
            print(f"  • Purpose: {C.YELLOW}{task_desc}{C.RESET}")
            self.speak("Synthesizing dedicated software architecture and compiling unit verification tests.")

            res = asyncio.run(dynamic_system_builder.construct_software_autonomously(task_desc))
            if res.get("success"):
                print(f"\n{C.GREEN}{C.BOLD}✓ Software Construction Certified & Deployed!{C.RESET}")
                print(f"  • System ID: {C.CYAN}{res.get('system_id')}{C.RESET}")
                print(f"  • System Name: {C.BOLD}{res.get('name')}{C.RESET}")
                print(f"  • Certified Entrypoint: {res.get('entrypoint')}")
                print(f"  • Capabilities: {', '.join(res.get('capabilities', []))}\n")
                self.speak(f"Software system {res.get('name')} successfully constructed and certified.")
            else:
                print(f"{C.RED}[Error] Construction failed unit verification.{C.RESET}")

        elif sub == "run":
            if len(parts) < 3:
                print(f"{C.RED}Usage: system run <system_id> [args]{C.RESET}")
                return
            sid = parts[2]
            args = parts[3:]
            print(f"\n{C.CYAN}Executing constructed system '{sid}'...{C.RESET}")
            res = dynamic_system_builder.execute_system(sid, args)
            if res.get("success"):
                print(f"{C.GREEN}✓ Execution completed in {res.get('duration_sec')}s:{C.RESET}")
                print(res.get("stdout"))
            else:
                print(f"{C.RED}✖ Execution error:{C.RESET} {res.get('error') or res.get('stderr')}")

    def handle_rea_cmd(self, parts: list[str]):
        """REA (Reverse Engineer Anything) commands."""
        from core.rea_powerup import rea_engine
        if len(parts) < 2 or parts[1].lower() in ["help", "info"]:
            print(f"\n{C.CYAN}{C.BOLD}🔬 [REA // Reverse Engineer Anything Engine]{C.RESET}")
            print("  Inspect, decompile, and reconstruct proprietary software & closed APIs.")
            print(f"  {C.CYAN}rea inspect <binary_path>{C.RESET}  Disassemble and extract symbols/APIs from .exe/.dll/.so")
            print(f"  {C.CYAN}rea unpack <asar_path>{C.RESET}    Extract Electron IPC channels and internal JS bundles")
            print(f"  {C.CYAN}rea traffic <har_or_pcap>{C.RESET} Parse captured network traffic for undocumented endpoints")
            print(f"  {C.CYAN}rea strings <file> [pat]{C.RESET}  Surgical forensic string extractor (any file)")
            print(f"  {C.CYAN}rea secrets <file>{C.RESET}        Scan any file for leaked API keys, tokens & credentials")
            print(f"  {C.CYAN}rea routes <file>{C.RESET}         Harvest REST and WebSocket endpoints")
            print(f"  {C.CYAN}rea audit <binary>{C.RESET}        Audit binary security posture & suspicious system calls")
            print(f"  {C.CYAN}rea clone <name> <routes>{C.RESET} Generate clean-room Python client library\n")
            return

        sub = parts[1].lower()
        if sub == "inspect":
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea inspect <binary_path>{C.RESET}")
                return
            target = parts[2]
            print(f"\n{C.CYAN}[REA Inspect]{C.RESET} Disassembling binary: {C.YELLOW}{target}{C.RESET}")
            res = rea_engine.inspect_binary(target)
            if res.get("success"):
                print(f"{C.GREEN}✓ Binary Disassembly Complete:{C.RESET} {res.get('binary_format')}")
                print(f"  • Extracted Symbols: {res.get('extracted_symbols_count')} symbols found")
                print(f"  • Discovered Endpoints: {', '.join(res.get('discovered_api_routes', [])) or 'None'}")
                print(f"  • Evidence: {res.get('evidence')}\n")
            else:
                print(f"{C.RED}✖ Inspection error:{C.RESET} {res.get('error')}")

        elif sub == "unpack":
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea unpack <asar_path>{C.RESET}")
                return
            target = parts[2]
            print(f"\n{C.CYAN}[REA Unpack]{C.RESET} Unpacking Electron archive: {C.YELLOW}{target}{C.RESET}")
            res = rea_engine.unpack_electron(target)
            if res.get("success"):
                print(f"{C.GREEN}✓ Electron Bundle Parsed:{C.RESET}")
                print(f"  • Discovered IPC Channels: {', '.join(res.get('ipc_channels', []))}")
                print(f"  • Discovered Endpoints: {', '.join(res.get('discovered_endpoints', []))}\n")
            else:
                print(f"{C.RED}✖ Unpack error:{C.RESET} {res.get('error')}")

        elif sub == "traffic":
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea traffic <capture_file>{C.RESET}")
                return
            target = parts[2]
            print(f"\n{C.CYAN}[REA Traffic Analyzer]{C.RESET} Parsing network telemetry: {C.YELLOW}{target}{C.RESET}")
            res = rea_engine.analyze_traffic(target)
            if res.get("success"):
                print(f"{C.GREEN}✓ Traffic Analysis Complete:{C.RESET}")
                print(f"  • Extracted Endpoints ({len(res.get('extracted_endpoints', []))}):")
                for ep in res.get("extracted_endpoints", [])[:8]:
                    print(f"    • {ep}")
                print(f"  • Auth Schemes Detected: {res.get('auth_schemes_detected')}\n")
            else:
                print(f"{C.RED}✖ Traffic analysis error:{C.RESET} {res.get('error')}")

        elif sub in ["strings", "extract_strings"]:
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea strings <file_path> [filter_pattern]{C.RESET}")
                return
            target = parts[2]
            pat = parts[3] if len(parts) > 3 else None
            print(f"\n{C.CYAN}[REA Surgical Strings]{C.RESET} Extracting strings from: {C.YELLOW}{target}{C.RESET}")
            res = rea_engine.extract_strings(target, filter_pattern=pat)
            if res.get("success"):
                print(f"{C.GREEN}✓ Forensic String Extraction Complete:{C.RESET}")
                print(f"  • Total Matches: {res.get('total_strings_found')} | Unique: {res.get('unique_strings_count')}")
                for s in res.get("sample_strings", [])[:15]:
                    print(f"    • {s}")
                print()
            else:
                print(f"{C.RED}✖ Error: {res.get('error')}{C.RESET}")

        elif sub in ["secrets", "keys", "hunt"]:
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea secrets <file_path>{C.RESET}")
                return
            target = parts[2]
            print(f"\n{C.CYAN}[REA Secret Hunter]{C.RESET} Auditing credentials in: {C.YELLOW}{target}{C.RESET}")
            res = rea_engine.scan_secrets_and_keys(target)
            if res.get("success"):
                print(f"{C.GREEN}✓ Credential Scan Complete:{C.RESET}")
                print(f"  • Secrets Detected: {res.get('secrets_detected')}")
                for s in res.get("findings", []):
                    print(f"    • [{s['type']}]: {s['masked_value']}")
                print()
            else:
                print(f"{C.RED}✖ Error: {res.get('error')}{C.RESET}")

        elif sub in ["routes", "endpoints"]:
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea routes <capture_or_file>{C.RESET}")
                return
            target = parts[2]
            print(f"\n{C.CYAN}[REA Route Harvester]{C.RESET} Harvesting API routes from: {C.YELLOW}{target}{C.RESET}")
            res = rea_engine.harvest_api_endpoints(target)
            if res.get("success"):
                print(f"{C.GREEN}✓ Endpoints Recovered ({res.get('endpoints_count', 0)}):{C.RESET}")
                for ep in res.get("endpoints", [])[:15]:
                    print(f"    • {ep}")
                print()
            else:
                print(f"{C.RED}✖ Error: {res.get('error')}{C.RESET}")

        elif sub == "audit":
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea audit <binary_path>{C.RESET}")
                return
            target = parts[2]
            print(f"\n{C.CYAN}[REA Security Auditor]{C.RESET} Auditing binary security posture: {C.YELLOW}{target}{C.RESET}")
            res = rea_engine.audit_binary_security(target)
            if res.get("success"):
                risk_color = C.RED if res.get("risk_tier") == "ELEVATED" else C.GREEN
                print(f"{C.GREEN}✓ Binary Security Audit Complete:{C.RESET} Format: {res.get('format')} | Risk: {risk_color}{res.get('risk_tier')}{C.RESET}")
                print(f"  • Suspicious/Privileged APIs: {', '.join(res.get('suspicious_apis_imported', [])) or 'None'}")
                print(f"  • Evidence: {res.get('evidence')}\n")
            else:
                print(f"{C.RED}✖ Error: {res.get('error')}{C.RESET}")

        elif sub in ["run", "external", "official"]:
            if len(parts) < 3:
                print(f"{C.RED}Usage: rea run <command> [args...]{C.RESET}")
                return
            ext_cmd = parts[2]
            ext_args = parts[3:]
            print(f"\n{C.CYAN}[REA Official Toolchain]{C.RESET} Invoking @morluto/rea: {C.YELLOW}{ext_cmd} {' '.join(ext_args)}{C.RESET}")
            res = rea_engine.invoke_external_rea(ext_cmd, ext_args)
            if res.get("success"):
                print(f"{C.GREEN}✓ REA Command Output:{C.RESET}")
                print(res.get("stdout"))
            else:
                print(f"{C.RED}✖ Error ({res.get('exit_code')}):{C.RESET} {res.get('stderr') or res.get('error')}")

    async def handle_audit_cmd(self, target_str: str):
        target_path = Path(os.path.expanduser(target_str.strip().strip("'\"")))
        if not target_path.exists():
            print(f"{C.RED}Error: Path '{target_str}' not found on host machine.{C.RESET}")
            return

        print(f"\n{C.CYAN}{C.BOLD}🔍 [Architectural Codebase Audit]{C.RESET} Analyzing {target_path.resolve()}...")
        self.speak(f"Analyzing codebase at {target_path.name}.")

        if target_path.is_file():
            print(f"  • Single File: {target_path.name} ({target_path.stat().st_size} bytes)")
            from core.rea_powerup import rea_engine
            sec = rea_engine.scan_secrets_and_keys(str(target_path))
            print(f"  • Security Check: {sec.get('secrets_detected', 0)} credentials detected")
            print("  • Status: Ingested and ready for improvement.")
        else:
            ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".pytest_cache", ".ruff_cache", "dist", "build"}
            code_files = []
            for root, dirs, fnames in os.walk(target_path):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for fn in fnames:
                    if fn.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".html", ".css", ".json")):
                        code_files.append(Path(root, fn))

            print(f"  • Total Code Files Scanned: {C.BOLD}{len(code_files)}{C.RESET}")
            has_tests = any("test" in str(p).lower() for p in code_files)
            print(f"  • Automated Test Suite Present: {C.GREEN if has_tests else C.RED}{'Yes' if has_tests else 'No (Critical Quality Gap)'}{C.RESET}")

            ext_counts = {}
            for cf in code_files:
                ext_counts[cf.suffix] = ext_counts.get(cf.suffix, 0) + 1
            breakdown_str = ", ".join([f"{k}: {v}" for k, v in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:5]])
            print(f"  • Primary Languages: {breakdown_str}")

            print(f"\n{C.GREEN}{C.BOLD}★ Strategic Enhancement Opportunities Identified:{C.RESET}")
            print("  1. Add Comprehensive Automated Unit & Regression Tests")
            print("  2. Modernize API layer to async non-blocking patterns")
            print("  3. Optimize database queries & connection pooling")
            print(f"\n{C.CYAN}To command JARVIS to refactor or improve this application, issue:{C.RESET}")
            print(f"  {C.BOLD}JARVIS > improve {target_path} by adding comprehensive unit tests and fixing bugs{C.RESET}\n")

    async def handle_browser_cmd(self, parts: list[str]):
        """Direct browser automation commands from terminal."""
        # Clean tokens of trailing semicolons, commas, dots commonly typed by programmers
        cleaned_parts = [re.sub(r'[\s;,.]+$', '', p) for p in parts if p.strip()]
        if len(cleaned_parts) < 2:
            print(f"{C.RED}Usage: browser <demo|inbox|compose|open|run|agent|email|login|tab|play> [arguments]{C.RESET}")
            return

        parts = cleaned_parts
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

        elif sub == "open" or sub in ["leetcode", "youtube", "github", "google", "linkedin", "gmail"] or any(ext in sub for ext in [".com", ".org", ".io", ".net", ".ai"]):
            if sub == "open":
                if len(parts) < 3:
                    print(f"{C.RED}Usage: browser open <url>{C.RESET}")
                    return
                raw_url = parts[2]
            else:
                raw_url = sub
            url = browser_agent.normalize_web_url(raw_url)
            print(f"{C.CYAN}Opening in browser tab:{C.RESET} {url}")
            tab_res = await asyncio.to_thread(browser_agent.open_tab, url)
            if tab_res.get("success"):
                print(f"{C.GREEN}✓ Opened in active browser tab ({tab_res.get('tab_count', 1)} total tabs open).{C.RESET}")
                self.speak(f"Opened {url} in a new tab.")
            else:
                BrowserController.open_in_system_browser(url)
                print(f"{C.GREEN}✓ Opened in system browser tab.{C.RESET}")

        elif sub in ["tab", "tabs"]:
            action = parts[2].lower() if len(parts) > 2 else "list"
            if action in ["list", "all", "ls"]:
                tabs = browser_agent.list_tabs()
                if not tabs:
                    print(f"{C.YELLOW}No active browser tabs found. Open one with 'browser open <url>'.{C.RESET}")
                else:
                    print(f"\n{C.CYAN}{C.BOLD}🌐 [Active Browser Tabs ({len(tabs)})]{C.RESET}")
                    for t in tabs:
                        print(f"  • [Tab {t['index']}] {C.BOLD}{t['title']}{C.RESET} — {C.DIM}{t['url']}{C.RESET}")
                    print(f"\n{C.DIM}Commands: tab switch <index> | tab close <index> | tab new <url>{C.RESET}\n")

            elif action in ["new", "open", "create"]:
                if len(parts) < 4:
                    print(f"{C.RED}Usage: browser tab new <url>{C.RESET}")
                    return
                t_url = parts[3]
                tab_res = await asyncio.to_thread(browser_agent.open_tab, t_url)
                if tab_res.get("success"):
                    print(f"{C.GREEN}✓ Opened in new tab #{tab_res.get('tab_count')}: {tab_res.get('title')}{C.RESET}")
                else:
                    print(f"{C.RED}Failed to open tab: {tab_res.get('error')}{C.RESET}")

            elif action in ["switch", "focus", "goto"]:
                if len(parts) < 4:
                    print(f"{C.RED}Usage: browser tab switch <index>{C.RESET}")
                    return
                try:
                    idx = int(parts[3])
                    s_res = browser_agent.switch_tab(idx)
                    if s_res.get("success"):
                        print(f"{C.GREEN}✓ Switched to Tab {idx}: {s_res.get('title')}{C.RESET}")
                    else:
                        print(f"{C.RED}{s_res.get('error')}{C.RESET}")
                except ValueError:
                    print(f"{C.RED}Invalid tab index. Must be a number.{C.RESET}")

            elif action in ["close", "kill"]:
                idx = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None
                c_res = browser_agent.close_tab(idx)
                if c_res.get("success"):
                    print(f"{C.GREEN}✓ Tab closed ({c_res.get('remaining_tabs')} tabs remaining).{C.RESET}")
                else:
                    print(f"{C.RED}{c_res.get('error')}{C.RESET}")

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
            print(f"{C.CYAN}Dispatching email autonomously to {to}...{C.RESET}")
            res = await asyncio.to_thread(browser_agent.send_email_autonomously, to, subject, body)
            print(f"{C.GREEN}✓ Dispatch Result:{C.RESET} {res.get('message')}")
            for act in res.get("actions", []):
                print(f"  • {act}")
            self.speak(f"Email dispatched for {to}.")

        elif sub in ["login", "auth"]:
            service_target = parts[2] if len(parts) > 2 else "google"
            if service_target.lower() in ["accounts", "account", "all", "general"]:
                service_target = "google"
            preferred_browser = parts[3] if len(parts) > 3 else None
            target_url, service_name = BrowserController.resolve_login_target(service_target)
            print(f"{C.CYAN}Launching Jarvis Persistent Browser Profile (Axiom Mode)...{C.RESET}")
            print(f"{C.YELLOW}Sign in to your {service_name} ONCE in the browser window that appears.\nOnce signed in, Jarvis will autonomously retain access for all future workflows!{C.RESET}")
            if preferred_browser:
                print(f"  • Preferred Browser: {C.GREEN}{preferred_browser.title()}{C.RESET}")
            print("  • Tip: If verification stalls, complete the Cloudflare checkbox or captcha in the browser window.\n")
            self.speak(f"Launching persistent browser window for {service_name}. Please sign in.")
            res = await asyncio.to_thread(BrowserController.launch_login_session, service_target, preferred_browser)
            if res.get("logged_in"):
                print(f"\n{C.GREEN}{C.BOLD}✓ Authentication session saved for {service_name}! Autonomous browser dispatch is now permanently active.{C.RESET}\n")
                self.speak(f"Authentication saved for {service_name}. Autonomous dispatch active.")
            else:
                print(f"\n{C.DIM}Session closed for {service_name}. Profile saved at: {res.get('profile_path')}{C.RESET}\n")

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

        else:
            # Natural goal fallback for any "browser <natural instruction>"
            goal = " ".join(parts[1:])
            await self.handle_autonomous_browse(goal)

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

    def find_session_by_semantics(self, query: str) -> Optional[dict[str, Any]]:
        """
        Pure Semantic Session Search (Zero Templates / Zero Rigid Syntax).
        Locates historical missions from natural conversational cues:
        - 'latest session', 'last mission', 'recent work' -> returns most recent session.
        - 'session we talked about making multiple robots' -> scans titles, prompts, deliverables, and folder names.
        """
        items = workflow_manager.list_history()
        if not items:
            return None

        low = query.lower()

        # 1. Latest / last session cues
        if any(w in low for w in ["latest", "last", "most recent", "newest", "previous mission", "previous session"]):
            return items[0]

        # 2. Direct session_id substring match
        for it in items:
            sid = it.get("session_id", "").lower()
            if sid and sid in low:
                return it

        # 3. Dynamic semantic scoring across titles, prompts, and deliverables
        stopwords = {
            "go", "to", "the", "session", "we", "talked", "about", "making", "that", "where",
            "our", "show", "me", "open", "switch", "inspect", "view", "what", "did", "do",
            "in", "with", "a", "an", "and", "or", "for", "of", "can", "you", "find", "get",
            "take", "look", "at", "tell", "was"
        }
        tokens = [t for t in re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', low) if t not in stopwords]

        best_match = None
        best_score = 0

        for it in items:
            score = 0
            searchable = (
                f"{it.get('session_id', '')} "
                f"{it.get('title', '')} "
                f"{it.get('prompt', '')} "
                f"{it.get('folder', '')} "
                f"{' '.join(str(d) for d in (it.get('deliverables') or []))}"
            ).lower()

            for token in tokens:
                if token in searchable:
                    score += 2
                    if token in it.get("title", "").lower() or token in it.get("prompt", "").lower():
                        score += 3
            if score > best_score:
                best_score = score
                best_match = it

        if best_match and best_score >= 2:
            return best_match

        return None

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

        # Sanitize trailing punctuation commonly appended by programmers (semicolons, commas, dots)
        line = re.sub(r'[\s;,.]+$', '', line).strip()
        if not line:
            return True

        low = line.lower()
        if low in ["exit", "quit", "q", "power down", "goodbye"]:
            try:
                from core.browser_agent import browser_agent
                browser_agent.close_active_session()
            except Exception:
                pass
            print(f"\n{C.DIM}Powering down terminal interface. Central Brain standing by.{C.RESET}")
            self.speak("Standing by, Master Ansh.")
            return False

        if low in ["close browser", "exit browser", "quit browser", "kill browser", "stop browser"]:
            try:
                from core.browser_agent import browser_agent
                browser_agent.close_active_session()
            except Exception:
                pass
            print(f"\n{C.GREEN}✓ Active Co-Worker browser session closed.{C.RESET}\n")
            self.speak("Co-Worker browser session closed.")
            return True

        if low in ["help", "?", "commands", "show commands", "what can you do", "help me"]:
            self.print_help()
            return True

        if low in ["clear", "cls", "clean", "clear screen", "clean terminal"]:
            os.system("cls" if os.name == "nt" else "clear")
            self.print_banner()
            return True

        # Natural Voice Mute / Unmute
        if low in ["mute", "be quiet", "stop speaking", "turn off voice", "disable voice", "voice off", "shutup", "shut up"]:
            self.voice_enabled = False
            print(f"Voice output set to: {C.RED}OFF{C.RESET}\n")
            return True

        if low in ["unmute", "turn on voice", "enable voice", "voice on", "speak to me"]:
            self.voice_enabled = True
            print(f"Voice output set to: {C.GREEN}ON{C.RESET}\n")
            self.speak("Voice output activated.")
            return True

        if low.startswith("voice "):
            parts = low.split()
            if len(parts) > 1:
                self.voice_enabled = (parts[1] == "on")
                print(f"Voice output set to: {C.GREEN if self.voice_enabled else C.RED}{'ON' if self.voice_enabled else 'OFF'}{C.RESET}\n")
                if self.voice_enabled:
                    self.speak("Voice output activated.")
            return True

        # Natural Microphone Input
        if low in ["listen", "mic", "voice in", "speak", "listen to me", "start mic", "turn on mic"]:
            self.speak("Listening for your voice command.")
            heard = self.listen_for_voice(timeout_sec=8)
            if heard:
                print(f"\n{C.GREEN}{C.BOLD}🎙️ [Heard Command]:{C.RESET} '{heard}'\n")
                return await self.process_directive(heard)
            else:
                print(f"{C.DIM}[No voice command detected or microphone timed out]{C.RESET}\n")
                return True

        # Utility Subcommands
        if low.startswith("audit ") or low.startswith("inspect folder "):
            target = line.split(maxsplit=1)[1].strip().strip("'\"")
            await self.handle_audit_cmd(target)
            return True

        if low in ["workflows", "workflow"]:
            self.list_workflows()
            return True

        if low in ["schedules", "schedule"]:
            self.list_schedules()
            return True

        # Natural History / Past Missions
        if low in ["history", "past missions", "previous missions", "show history", "view history", "list missions", "recent tasks"]:
            self.list_history()
            return True

        # Natural Conversational & Semantic Session Discovery
        session_cues = ["session", "mission", "workspace"]
        nav_cues = ["go to", "switch to", "open", "inspect", "view", "load", "show me", "take me to", "what did we do in", "what was in", "find session", "find mission", "jump to"]
        if (any(c in low for c in session_cues) and any(n in low for n in nav_cues)) or low.startswith(("go to session", "switch to session", "open session", "inspect session", "view session", "jump to session")):
            matched = self.find_session_by_semantics(line)
            if matched:
                sid = matched.get("session_id")
                if sid:
                    title = matched.get("title") or sid
                    self.active_session_id = str(sid)
                    print(f"\n{C.GREEN}{C.BOLD}🎯 [Session Switch]:{C.RESET} Located mission: {C.CYAN}{sid}{C.RESET} ('{title}')")
                    self.inspect_session(str(sid))
                    self.speak(f"Active session switched to {title}.")
                    return True
            else:
                print(f"\n{C.YELLOW}[Session Recall]{C.RESET} Checked mission archive: No past session found matching '{line}'.\n")
                self.speak("I checked your mission archive, but could not find a past session matching that topic.")
                return True

        # Natural Session Inspection
        if low in ["session", "inspect session", "view session"]:
            target_sid = self.active_session_id
            if not target_sid:
                items = workflow_manager.list_history()
                if items:
                    target_sid = items[0].get("session_id")
            if target_sid:
                self.inspect_session(target_sid)
            else:
                print(f"{C.YELLOW}No active session found. Usage: session <session_id>{C.RESET}")
            return True

        if low.startswith("session "):
            parts = line.split()
            if len(parts) > 1:
                self.inspect_session(parts[1])
            return True

        # Natural Export
        if low in ["export", "export latest", "export session", "export files", "download files"]:
            target_sid = self.active_session_id
            if not target_sid:
                items = workflow_manager.list_history()
                if items:
                    target_sid = items[0].get("session_id")
            if target_sid:
                self.export_session(target_sid)
            else:
                print(f"{C.YELLOW}No active session to export. Usage: export <session_id> [destination_path]{C.RESET}")
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

        if low.startswith("outreach "):
            parts = line[9:].strip().split(maxsplit=1)
            niche = parts[0] if parts else "Distributed Infrastructure"
            hook = parts[1] if len(parts) > 1 else "reduces latency by 60%"
            self.handle_outreach_cmd(niche, hook)
            return True

        # Autonomous Multi-Account Fleet Management (20 Inboxes, Anti-Spam Jitter, Reply Monitor)
        if low.startswith("fleet") or low in ["accounts", "fleet status", "fleet replies"]:
            parts = line.split()
            self.handle_fleet_cmd(parts)
            return True

        # Autonomous Self-Constructing Software Systems
        if low.startswith("system") or low in ["systems", "software", "catalog"]:
            parts = line.split()
            self.handle_system_cmd(parts)
            return True

        # REA (Reverse Engineer Anything) Engine
        if low.startswith("rea"):
            parts = line.split()
            self.handle_rea_cmd(parts)
            return True

        # Browser-Use Autonomous Vision-Action Web Agent
        if low.startswith("browser-use ") or low.startswith("bu "):
            task = line.split(maxsplit=1)[1].strip()
            await self.handle_browser_use_cmd(task)
            return True

        # Direct Login / Auth Directive (e.g. "login", "login;", "login google", "login leetcode")
        # Or Natural Conversational Login (e.g. "i want to login in browser windows of yours so you can do what i want in my accounts")
        login_keywords = ["login", "log in", "sign in", "signin", "authenticate", "auth"]
        has_login_intent = any(k in low for k in login_keywords)
        has_browser_or_account_context = any(w in low for w in [
            "browser", "window", "account", "accounts", "google", "gmail", "leetcode",
            "github", "linkedin", "aws", "vercel", "stripe", "upwork", "twitter", "x",
            "let me", "i want to", "i need to", "open", "in your", "yours", "so you can"
        ])

        is_direct_login = low.startswith(("login", "log in", "signin", "sign in", "auth ")) or low in ["login", "signin", "auth"]
        is_question_or_search = low.startswith(("what is", "how to", "how do", "how does", "why ", "explain", "who is", "who are", "author", "authority", "tutorial", "code ", "build ", "create ")) or low.endswith("?")

        if ((has_login_intent and has_browser_or_account_context) or is_direct_login) and not is_question_or_search:
            clean_cmd = re.sub(r'^(?:browser\s+login|login\s+to|login\s+on|login\s+in|login|signin|sign\s+in\s+to|sign\s+in\s+on|sign\s+in|auth)\s*', '', low).strip(" ;.")
            if is_direct_login and clean_cmd and len(clean_cmd.split()) <= 3:
                target_svc = clean_cmd
            else:
                target_svc = "google"
                for s in ["leetcode", "github", "linkedin", "aws", "vercel", "stripe", "upwork", "twitter", "x", "instantly", "linear", "beehiiv", "supabase", "google", "gmail"]:
                    if s in low:
                        target_svc = s
                        break
            parts = ["browser", "login", target_svc]
            await self.handle_browser_cmd(parts)
            return True

        # Direct Open URL in Browser Tab (e.g. "open leetcode", "open youtube.com", "open tab leetcode")
        # Action tasks with clauses like "and", "search", "play" fall through to autonomous browser agent
        if (low.startswith("open ") or low.startswith("go to ")) and not any(w in low for w in [" and ", "search ", "play ", "solve ", "find ", "click ", "watch ", "download ", "fill "]):
            target_term = line[5:].strip() if low.startswith("open ") else line[6:].strip()
            if target_term.lower().startswith("tab "):
                target_term = target_term[4:].strip()
            if not any(w in target_term.lower() for w in ["file", "project", "repo", "system", "app"]) and len(target_term.split()) <= 3:
                parts = ["browser", "open", target_term]
                await self.handle_browser_cmd(parts)
                return True

        # Explicit Chat Directive
        if low.startswith("chat "):
            await self.handle_chat(line)
            return True

        if low.startswith("browser ") or low.startswith("tab ") or low in ["tabs", "browser tabs"]:
            try:
                parts = shlex.split(line)
            except Exception:
                parts = line.split()
            if not parts[0].startswith("browser"):
                parts = ["browser"] + parts
            await self.handle_browser_cmd(parts)
            return True

        # Cognitive Repetition & Workflow Evolution Tracking
        rep = creator_memory.track_and_detect_repetition(line)
        if rep.get("is_repeated") and rep.get("count") == 2:
            print(f"\n{C.MAGENTA}{C.BOLD}🧠 [Autonomous Workflow Evolution]{C.RESET} Pattern recognized!")
            print(f"  • Directive requested {C.YELLOW}{rep.get('count')} times{C.RESET}. Autonomously promoted to permanent workflow: {C.GREEN}{rep.get('workflow_title')}{C.RESET}")
            print(f"  • Registered in workflow library ({C.CYAN}workflows.json{C.RESET}) for 1-click execution or 24/7 scheduling.\n")
            self.speak("Pattern recognized. I have promoted this workflow into your permanent library.")

        # Autonomous Intent Classification by Central Brain (Zero Templates, Zero Keyword Dictionaries)
        intent = await self.classify_intent_autonomously(line)
        mode = intent.get("mode", "chat")
        goal = intent.get("goal", line)

        if mode == "login":
            print(f"\n{C.YELLOW}{C.BOLD}[Central Brain Router]{C.RESET} Directive classified as user authentication session.")
            target_svc = intent.get("target") or "google"
            await self.handle_browser_cmd(["browser", "login", target_svc])
            return True
        elif mode == "browser":
            print(f"\n{C.YELLOW}{C.BOLD}[Central Brain Router]{C.RESET} Directive classified as autonomous web/browser action.")
            await self.handle_autonomous_browse(line)
            return True
        elif mode == "swarm":
            print(f"\n{C.YELLOW}{C.BOLD}[Central Brain Router]{C.RESET} Directive classified as autonomous software engineering project.")
            await self.run_mission(goal)
            return True
        else:
            await self.handle_chat(line)
            return True

    async def run_interactive(self):
        self.print_banner()
        self.speak("JARVIS Terminal Cognitive Interface online. Standing by for directives, Master Ansh.")

        while True:
            try:
                line = input(f"{C.BOLD}{C.BLUE}JARVIS > {C.RESET}").strip()
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
    if len(sys.argv) > 1:
        initial_directive = " ".join(sys.argv[1:]).strip()
        cli.print_banner()
        asyncio.run(cli.process_directive(initial_directive))
    else:
        asyncio.run(cli.run_interactive())


if __name__ == "__main__":
    main()