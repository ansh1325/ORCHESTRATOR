"""
JARVIS Terminal & Git Execution Engine
========================================
Full Autonomous Terminal and Git Interface for JARVIS:
1. Direct Command Execution: Subprocess execution with real-time stdout/stderr,
   smart Python/Pip binary routing, timeout control, and safety guards.
2. Autonomous Git Lifecycle:
   - Status, Diff, Log inspection.
   - Autonomous semantic commit message synthesis based on git diff.
   - Stage (`git add -A`), Commit (`git commit -m "..."`), and Remote Push (`git push`).
3. Visible Desktop Terminal Spawning:
   - Spawns real, interactive Windows Terminal (`wt.exe` / `powershell.exe` / `cmd.exe`)
     windows on Master Ansh's screen for live inspection.
"""

import os
import sys
import re
import time
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List

logger = logging.getLogger("Jarvis.TerminalEngine")


class TerminalEngine:
    """
    Central Terminal & Git Lifecycle Controller for JARVIS.
    Enables JARVIS to open terminals, run shell directives, and manage git repositories autonomously.
    """

    DEFAULT_WORKSPACE = Path(__file__).resolve().parent.parent

    DANGEROUS_PATTERNS = [
        r'\bformat\s+[a-z]:',
        r'\bdel\s+/[sfq]\s+[a-z]:\\windows',
        r'\brmdir\s+/[sq]\s+[a-z]:\\windows',
        r'\brm\s+-rf\s+/(?:etc|usr|bin|var|boot)?$',
        r'\bshutdown\s+/[sfrt]'
    ]

    @classmethod
    def get_workspace(cls, cwd: Optional[str] = None) -> Path:
        """Resolves target workspace directory."""
        if cwd:
            p = Path(cwd).resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p
        return cls.DEFAULT_WORKSPACE

    @classmethod
    def run_command(
        cls,
        command: str,
        cwd: Optional[str] = None,
        timeout_sec: int = 120,
        env: Optional[dict] = None
    ) -> dict[str, Any]:
        """
        Executes a shell command in the workspace and returns structured execution metrics.
        """
        target_dir = cls.get_workspace(cwd)
        cmd_str = command.strip()

        # Check safety guard
        low_cmd = cmd_str.lower()
        for pat in cls.DANGEROUS_PATTERNS:
            if re.search(pat, low_cmd):
                return {
                    "success": False,
                    "returncode": -1,
                    "command": cmd_str,
                    "stdout": "",
                    "stderr": f"Security Alert: Command blocked by PortSafetyGuard (matches forbidden pattern '{pat}').",
                    "duration_sec": 0.0
                }

        # Route python / pip / pytest invocations to active interpreter
        exec_cmd = cmd_str
        if exec_cmd.startswith("python "):
            exec_cmd = f'"{sys.executable}" ' + exec_cmd[7:]
        elif exec_cmd.startswith("python3 "):
            exec_cmd = f'"{sys.executable}" ' + exec_cmd[8:]
        elif exec_cmd.startswith("pytest ") or exec_cmd == "pytest":
            exec_cmd = f'"{sys.executable}" -m pytest' + exec_cmd[6:]
        elif exec_cmd.startswith("pip "):
            exec_cmd = f'"{sys.executable}" -m pip ' + exec_cmd[4:]

        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        t_start = time.perf_counter()
        try:
            res = subprocess.run(
                exec_cmd,
                cwd=str(target_dir),
                shell=True,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=merged_env,
                encoding="utf-8",
                errors="replace"
            )
            duration = round(time.perf_counter() - t_start, 3)
            return {
                "success": res.returncode == 0,
                "returncode": res.returncode,
                "command": cmd_str,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "duration_sec": duration,
                "cwd": str(target_dir)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": 124,
                "command": cmd_str,
                "stdout": "",
                "stderr": f"Command execution timed out after {timeout_sec}s.",
                "duration_sec": timeout_sec,
                "cwd": str(target_dir)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "command": cmd_str,
                "stdout": "",
                "stderr": f"Subprocess execution error: {e}",
                "duration_sec": round(time.perf_counter() - t_start, 3),
                "cwd": str(target_dir)
            }

    # ── Git Automation Suite ──

    @classmethod
    def git_status(cls, cwd: Optional[str] = None) -> dict[str, Any]:
        """Returns structured git repository status."""
        target_dir = cls.get_workspace(cwd)
        # Check if inside git repo
        check = cls.run_command("git rev-parse --is-inside-work-tree", cwd=str(target_dir))
        if not check["success"]:
            return {
                "is_git_repo": False,
                "branch": None,
                "clean": True,
                "modified": [],
                "untracked": [],
                "error": "Directory is not a git repository."
            }

        branch_res = cls.run_command("git branch --show-current", cwd=str(target_dir))
        branch = branch_res["stdout"].strip() or "main"

        status_res = cls.run_command("git status --porcelain", cwd=str(target_dir))
        lines = [l for l in status_res["stdout"].splitlines() if l.strip()]

        modified: list[str] = []
        untracked: list[str] = []
        staged: list[str] = []

        for l in lines:
            code = l[:2]
            filename = l[3:].strip().strip('"')
            if code in ["M ", "A ", "D ", "R "]:
                staged.append(filename)
            elif "M" in code:
                modified.append(filename)
            elif "??" in code:
                untracked.append(filename)
            elif "D" in code:
                modified.append(filename)

        return {
            "is_git_repo": True,
            "branch": branch,
            "clean": len(lines) == 0,
            "total_changed": len(lines),
            "staged": staged,
            "modified": modified,
            "untracked": untracked,
            "raw_status": status_res["stdout"]
        }

    @classmethod
    def git_diff(cls, cached: bool = False, cwd: Optional[str] = None) -> str:
        """Returns the current git diff text."""
        cmd = "git diff --cached" if cached else "git diff"
        res = cls.run_command(cmd, cwd=cwd)
        return res["stdout"] if res["success"] else res["stderr"]

    @classmethod
    def git_log(cls, limit: int = 5, cwd: Optional[str] = None) -> list[dict[str, str]]:
        """Returns recent git commit history."""
        cmd = f'git log -n {limit} --pretty=format:"%h|%an|%ar|%s"'
        res = cls.run_command(cmd, cwd=cwd)
        if not res["success"] or not res["stdout"].strip():
            return []

        commits = []
        for line in res["stdout"].splitlines():
            parts = line.split("|", maxsplit=3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "relative_date": parts[2],
                    "message": parts[3]
                })
        return commits

    @classmethod
    def synthesize_semantic_commit_message(cls, cwd: Optional[str] = None) -> str:
        """
        Autonomously synthesizes a high-level, conventional commit message based on git diff.
        """
        stat_res = cls.run_command("git status --short", cwd=cwd)
        diff_stat = cls.run_command("git diff --stat", cwd=cwd)
        summary = stat_res["stdout"].strip() + "\n" + diff_stat["stdout"].strip()

        # If LLM is available, generate semantic message
        try:
            from core.config import settings
            llm = settings.get_llm_client()
            if llm and not settings.is_mock():
                prompt = (
                    "You are JARVIS Git Engine. Synthesize a concise, conventional commit message "
                    "(e.g. 'feat(core): add feature' or 'fix(cli): resolve routing') under 72 chars "
                    "summarizing these file changes:\n\n"
                    f"{summary[:1500]}"
                )
                resp = settings.create_chat_completion(
                    messages=[
                        {"role": "system", "content": "Output only the commit message subject line. Zero quotes, zero markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                msg = resp.choices[0].message.content.strip().strip('"\'')
                if msg and len(msg) < 100:
                    return msg
        except Exception:
            pass

        # Smart rule-based fallback based on changed filenames
        low = summary.lower()
        if "crawl4ai" in low:
            return "feat(crawler): integrate Crawl4AI stealth web scraping engine"
        elif "agent_reach" in low or "reach" in low:
            return "feat(reach): integrate Agent-Reach multi-platform intelligence"
        elif "test" in low and ("fix" in low or "assert" in low):
            return "test: enhance regression test suite and validation coverage"
        elif "cli" in low:
            return "feat(cli): expand autonomous central brain directives"
        return f"chore(jarvis): autonomous system enhancements ({len(stat_res['stdout'].splitlines())} files updated)"

    @classmethod
    def git_commit_and_push(
        cls,
        commit_message: Optional[str] = None,
        branch: Optional[str] = None,
        push: bool = True,
        add_all: bool = True,
        remote: str = "origin",
        cwd: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Full Autonomous Git Lifecycle:
        1. Checks status.
        2. Stages files (git add -A).
        3. Synthesizes semantic commit message if omitted.
        4. Commits changes.
        5. Pushes to remote GitHub repository.
        """
        target_dir = cls.get_workspace(cwd)
        status = cls.git_status(cwd=str(target_dir))
        if not status["is_git_repo"]:
            return {
                "success": False,
                "error": "Target directory is not a git repository."
            }

        target_branch = branch or status["branch"] or "main"

        # If nothing changed
        if status["clean"]:
            return {
                "success": True,
                "committed": False,
                "pushed": False,
                "branch": target_branch,
                "commit_hash": None,
                "commit_message": None,
                "message": "Working tree clean; no changes to commit."
            }

        # 1. Stage files
        if add_all:
            add_res = cls.run_command("git add -A", cwd=str(target_dir))
            if not add_res["success"]:
                return {"success": False, "error": f"Failed to stage files: {add_res['stderr']}"}

        # 2. Formulate commit message
        msg = commit_message or cls.synthesize_semantic_commit_message(cwd=str(target_dir))
        safe_msg = msg.replace('"', '\\"')

        # 3. Commit
        commit_res = cls.run_command(f'git commit -m "{safe_msg}"', cwd=str(target_dir))
        if not commit_res["success"]:
            # Check if there was genuinely nothing to commit
            if "nothing to commit" in commit_res["stdout"].lower() or "nothing to commit" in commit_res["stderr"].lower():
                return {
                    "success": True,
                    "committed": False,
                    "pushed": False,
                    "branch": target_branch,
                    "message": "Nothing to commit."
                }
            return {"success": False, "error": f"Git commit failed: {commit_res['stderr'] or commit_res['stdout']}"}

        # Get commit hash
        hash_res = cls.run_command("git rev-parse --short HEAD", cwd=str(target_dir))
        commit_hash = hash_res["stdout"].strip() if hash_res["success"] else "HEAD"

        push_ok = False
        push_output = ""
        if push:
            push_res = cls.run_command(f"git push {remote} {target_branch}", cwd=str(target_dir), timeout_sec=60)
            push_ok = push_res["success"]
            push_output = push_res["stdout"] or push_res["stderr"]

        return {
            "success": True,
            "committed": True,
            "pushed": push_ok if push else False,
            "commit_hash": commit_hash,
            "commit_message": msg,
            "branch": target_branch,
            "remote": remote,
            "push_output": push_output,
            "files_committed": status["total_changed"]
        }

    # ── Visible Terminal Spawner ──

    @classmethod
    def open_visible_terminal(
        cls,
        cwd: Optional[str] = None,
        command: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Spawns a real, interactive desktop terminal window on Master Ansh's screen.
        Tries Windows Terminal (wt.exe), then PowerShell, then CMD.
        """
        target_dir = cls.get_workspace(cwd)
        str_dir = str(target_dir)

        try:
            if sys.platform == "win32":
                # Check for Windows Terminal
                wt_bin = shutil.which("wt.exe") or shutil.which("wt")
                if wt_bin:
                    if command:
                        cmd_args = [wt_bin, "-d", str_dir, "powershell", "-NoExit", "-Command", command]
                    else:
                        cmd_args = [wt_bin, "-d", str_dir]
                    proc = subprocess.Popen(cmd_args)
                    return {"success": True, "terminal": "Windows Terminal (wt.exe)", "pid": proc.pid, "cwd": str_dir}

                # Fallback to PowerShell
                ps_bin = shutil.which("powershell.exe") or "powershell.exe"
                if command:
                    cmd_args = ["start", "powershell", "-NoExit", "-Command", f"Set-Location '{str_dir}'; {command}"]
                else:
                    cmd_args = ["start", "powershell", "-NoExit", "-Command", f"Set-Location '{str_dir}'"]
                subprocess.Popen(" ".join(cmd_args), shell=True)
                return {"success": True, "terminal": "Windows PowerShell", "cwd": str_dir}

            else:
                # Linux / macOS
                for term in ["x-terminal-emulator", "gnome-terminal", "konsole", "xterm"]:
                    term_bin = shutil.which(term)
                    if term_bin:
                        subprocess.Popen([term_bin, "--working-directory", str_dir])
                        return {"success": True, "terminal": term, "cwd": str_dir}

                return {"success": False, "error": "No GUI terminal emulator found on this host."}
        except Exception as e:
            logger.error(f"Failed to open visible terminal: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def doctor(cls) -> dict[str, Any]:
        """Diagnostics for shell environment and git readiness."""
        git_ver_res = cls.run_command("git --version")
        git_installed = git_ver_res["success"]
        git_ver = git_ver_res["stdout"].strip() if git_installed else "Not installed"

        shell_name = "PowerShell / cmd.exe" if sys.platform == "win32" else "bash / sh"
        ws = cls.get_workspace()
        status = cls.git_status(str(ws))

        return {
            "git_installed": git_installed,
            "git_version": git_ver,
            "default_shell": shell_name,
            "python_executable": sys.executable,
            "workspace_path": str(ws),
            "is_git_repo": status.get("is_git_repo", False),
            "active_branch": status.get("branch"),
            "uncommitted_changes": status.get("total_changed", 0),
            "status": "ONLINE"
        }


terminal_engine = TerminalEngine()

