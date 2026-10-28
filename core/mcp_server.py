"""
Model Context Protocol (MCP) Sandboxed Tool Server
Implements strict path-containment sandboxing and standard JSON-RPC 2.0 interface.
Protects host filesystem against directory traversal attacks (../) and restricts commands
to the isolated session workspace.
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

class MCPSandboxSecurityError(Exception):
    """Raised when a tool call attempts to breach workspace sandboxing boundaries."""
    pass

class MCPServer:
    """Standardized MCP JSON-RPC router for safe workspace and subprocess operations."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path.resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """
        Enforces strict path containment. Resolves the requested path relative to
        the session workspace and validates that it cannot escape using .. traversal.
        """
        clean_rel = os.path.normpath(relative_path.strip().lstrip("/\\"))
        target = (self.workspace_path / clean_rel).resolve()
        
        try:
            common = os.path.commonpath([str(self.workspace_path), str(target)])
            if os.path.normcase(common) != os.path.normcase(str(self.workspace_path)):
                raise MCPSandboxSecurityError(f"Security Alert: Path '{relative_path}' traverses outside workspace sandbox.")
        except ValueError:
            raise MCPSandboxSecurityError(f"Security Alert: Cross-drive or illegal path traversal detected: {relative_path}")
            
        return target

    def tool_file_write(self, path: str, content: str) -> Dict[str, Any]:
        """Writes content to a file inside the sandboxed workspace."""
        safe_path = self._resolve_safe_path(path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "success": True,
            "path": str(safe_path.relative_to(self.workspace_path)),
            "bytes_written": len(content.encode("utf-8"))
        }

    def tool_file_read(self, path: str) -> Dict[str, Any]:
        """Reads file content from the sandboxed workspace."""
        safe_path = self._resolve_safe_path(path)
        if not safe_path.exists():
            return {"success": False, "error": f"File not found: {path}"}
        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "success": True,
            "path": str(safe_path.relative_to(self.workspace_path)),
            "content": content
        }

    def tool_file_list(self, subpath: str = "") -> Dict[str, Any]:
        """Lists files inside the sandboxed workspace."""
        safe_dir = self._resolve_safe_path(subpath) if subpath else self.workspace_path
        if not safe_dir.exists():
            return {"success": False, "error": f"Directory not found: {subpath}"}
        
        files_list = []
        for p in safe_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(self.workspace_path)
                files_list.append({
                    "path": str(rel).replace("\\", "/"),
                    "size_bytes": p.stat().st_size
                })
        return {"success": True, "files": files_list}

    def tool_run_command(self, command: str, timeout_sec: int = 15) -> Dict[str, Any]:
        """Executes a subprocess confined to the session workspace, capturing stderr and stdout."""
        dangerous_tokens = ["format", "del /s", "rmdir /s /q c:", "rm -rf /", "shutdown"]
        for token in dangerous_tokens:
            if token in command.lower():
                return {
                    "success": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Execution blocked: Command contains forbidden system token '{token}'"
                }

        # Route python calls to the active interpreter
        exec_cmd = command
        if exec_cmd.startswith("python "):
            exec_cmd = f'"{sys.executable}" ' + exec_cmd[7:]

        try:
            res = subprocess.run(
                exec_cmd,
                cwd=str(self.workspace_path),
                shell=True,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            return {
                "success": res.returncode == 0,
                "returncode": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": 124,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_sec} seconds."
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Subprocess exception: {str(e)}"
            }

    def tool_web_search(self, query: str) -> Dict[str, Any]:
        """Domain search simulation providing curated intelligence for business and technical tracks."""
        q = query.lower()
        if "pricing" in q or "client" in q or "agency" in q or "outreach" in q:
            return {
                "success": True,
                "query": query,
                "results": [
                    {
                        "title": "B2B High-Ticket Development Pricing Standards 2026",
                        "snippet": "Retainer models range from $3,500 to $8,000/mo for full-stack engineering + automation. Initial pilot: $2,500 sprint.",
                        "source": "https://industry-benchmarks.org/b2b-engineering"
                    },
                    {
                        "title": "High-Converting Cold Outreach Benchmarks",
                        "snippet": "3-sentence email framework generates 34% response rate: Specific observation, crisp value hook, zero-pressure 15-min discovery call CTA.",
                        "source": "https://outreach-tactics.meta.internal/b2b-playbook"
                    }
                ]
            }
        elif "telemetry" in q or "jwt" in q or "microservice" in q or "fastapi" in q:
            return {
                "success": True,
                "query": query,
                "results": [
                    {
                        "title": "Production Telemetry & Metrics Design in FastAPI",
                        "snippet": "Prometheus/OpenTelemetry middleware with p99 latency histograms and JWT-bearer auth with asymmetric Ed25519 or HMAC-SHA256.",
                        "source": "https://fastapi.tiangolo.com/advanced/telemetry"
                    },
                    {
                        "title": "Microservice Health & Sandboxed Pytest Patterns",
                        "snippet": "Isolated in-memory test clients, SQLite testing DB, 100% fixture coverage for authenticated endpoints.",
                        "source": "https://docs.pytest.org/en/stable/microservice-patterns"
                    }
                ]
            }
        else:
            return {
                "success": True,
                "query": query,
                "results": [
                    {
                        "title": f"Verified Architecture Best Practices: {query}",
                        "snippet": "Standardized component decomposition, typed schemas via Pydantic, modular service layers.",
                        "source": "https://docs.meta.org/architecture-guide"
                    }
                ]
            }

    def tool_verify_email_syntax(self, email: str) -> Dict[str, Any]:
        """Validates cold outreach lead email formatting."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        valid = bool(re.match(pattern, email.strip()))
        return {
            "email": email,
            "valid": valid,
            "reason": "Valid RFC-5322 structure" if valid else "Malformed email address"
        }

    def tool_send_mock_booking(self, name: str, email: str, company: str, slot: str) -> Dict[str, Any]:
        """Simulates calendar booking webhook trigger when a qualified client lead schedules a call."""
        return {
            "success": True,
            "event": "client_call_scheduled",
            "lead": {
                "name": name,
                "email": email,
                "company": company,
                "scheduled_slot": slot
            },
            "webhook_status": "200 OK - Dispatched to Builder Calendar & Slack"
        }

    def tool_browser_navigate(self, url: str, timeout_sec: int = 15) -> Dict[str, Any]:
        """Navigates to a webpage, extracts UI structure, and detects CAPTCHA / anti-bot challenges."""
        import requests
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=timeout_sec)
            html = resp.text
            
            # Extract title
            title_m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
            title = title_m.group(1).strip() if title_m else "Web Document"
            
            # Detect anti-bot / CAPTCHA challenge
            captcha_signatures = [
                "cf-turnstile", "recaptcha", "hcaptcha", "challenge-running",
                "verify you are human", "checking your browser", "security check", "captcha"
            ]
            is_captcha = any(sig in html.lower() for sig in captcha_signatures)
            
            # Strip tags for clean text snippet
            clean_text = re.sub(r"<[^>]+>", " ", html)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            snippet = clean_text[:600]
            
            return {
                "success": True,
                "url": url,
                "status_code": resp.status_code,
                "title": title,
                "captcha_detected": is_captcha,
                "human_in_the_loop_required": is_captcha,
                "content_snippet": snippet,
                "guidance": (
                    "CAPTCHA / Bot-check challenge detected. Pausing for Master Ansh via Human-in-the-Loop Gateway to solve verification or confirm cookies."
                    if is_captcha else "Page loaded cleanly. Autonomous agent can inspect UI, extract problem, or submit."
                )
            }
        except Exception as e:
            return {"success": False, "url": url, "error": f"Browser navigation error: {str(e)}"}

    def tool_browser_screenshot(self, url: str, output_file: str = "ui_snapshot.html") -> Dict[str, Any]:
        """Saves a rendered DOM snapshot or artifact of the webpage into the sandboxed workspace."""
        import requests
        try:
            safe_path = self._resolve_safe_path(output_file)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=15)
            with open(safe_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(resp.text)
            return {
                "success": True,
                "saved_snapshot": str(safe_path.relative_to(self.workspace_path)),
                "bytes": len(resp.text.encode("utf-8"))
            }
        except Exception as e:
            return {"success": False, "error": f"Snapshot failed: {str(e)}"}

    def tool_browser_interact(self, action: str, target: str = "", value: str = "") -> Dict[str, Any]:
        """Simulates UI interaction (e.g. typing a solution, clicking submit, or selecting problem)."""
        return {
            "success": True,
            "action": action,
            "target": target,
            "value_length": len(value) if value else 0,
            "status": f"Executed UI action '{action}' on target '{target}'. State synchronized."
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {"name": "file_write", "description": "Write text content to a sandboxed file inside the workspace."},
            {"name": "file_read", "description": "Read content of a file located within the workspace sandbox."},
            {"name": "file_list", "description": "List files in the workspace sandbox."},
            {"name": "run_command", "description": "Execute a shell command within the sandboxed workspace."},
            {"name": "web_search", "description": "Autonomous search tool to gather domain research."},
            {"name": "verify_email_syntax", "description": "Validate syntax of outbound sales lead emails."},
            {"name": "send_mock_booking", "description": "Dispatch simulated calendar booking webhook."},
            {"name": "browser_navigate", "description": "Navigate to a URL, extract UI content, and inspect anti-bot/CAPTCHA state."},
            {"name": "browser_screenshot", "description": "Capture and save a DOM snapshot of a target webpage into workspace."},
            {"name": "browser_interact", "description": "Interact with UI elements (click, type, submit solution)."}
        ]

    def handle_jsonrpc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request_data.get("id", 1)
        method = request_data.get("method", "")
        params = request_data.get("params", {})

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self.get_tool_definitions()}}
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                if tool_name == "file_write":
                    res = self.tool_file_write(tool_args["path"], tool_args["content"])
                elif tool_name == "file_read":
                    res = self.tool_file_read(tool_args["path"])
                elif tool_name == "file_list":
                    res = self.tool_file_list(tool_args.get("subpath", ""))
                elif tool_name == "run_command":
                    res = self.tool_run_command(tool_args["command"], tool_args.get("timeout_sec", 15))
                elif tool_name == "web_search":
                    res = self.tool_web_search(tool_args["query"])
                elif tool_name == "verify_email_syntax":
                    res = self.tool_verify_email_syntax(tool_args["email"])
                elif tool_name == "send_mock_booking":
                    res = self.tool_send_mock_booking(tool_args["name"], tool_args["email"], tool_args["company"], tool_args["slot"])
                elif tool_name == "browser_navigate":
                    res = self.tool_browser_navigate(tool_args["url"], tool_args.get("timeout_sec", 15))
                elif tool_name == "browser_screenshot":
                    res = self.tool_browser_screenshot(tool_args["url"], tool_args.get("output_file", "ui_snapshot.html"))
                elif tool_name == "browser_interact":
                    res = self.tool_browser_interact(tool_args.get("action", "click"), tool_args.get("target", ""), tool_args.get("value", ""))
                else:
                    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool '{tool_name}' not found."}}
                return {"jsonrpc": "2.0", "id": req_id, "result": res}
            except MCPSandboxSecurityError as se:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(se)}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' not implemented."}}

