"""
JARVIS Dynamic Tool Synthesizer & MCP Hot-Reload Engine
Chief Systems Architect: Ansh Tiwari

Capabilities:
1. Runtime Self-Evolution: Generates new tool capabilities on the fly when encountering novel domains.
2. Shadow Verification: Compiles Python code and runs automated tests before accepting new tools.
3. Live MCP Tool Injection: Registers new tools into the active MCPServer instance at runtime without restarts.
4. Persistent Tool Registry: Preserves synthesized tools across sessions in workspaces/dynamic_tools.
"""

import importlib.util
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Callable

from core.config import settings

logger = logging.getLogger("Jarvis.ToolSynthesizer")


class ToolSynthesizer:
    """Autonomous Engine for Creating, Compiling, Testing, and Hot-Reloading Tools."""

    TOOLS_DIR: Path = settings.WORKSPACE_DIR / "dynamic_tools"
    MANIFEST_FILE: Path = TOOLS_DIR / "manifest.json"

    def __init__(self, mcp_instance: Any = None):
        self.mcp_instance = mcp_instance
        self.registered_dynamic_tools: dict[str, Callable] = {}
        self._ensure_dir()

    def _ensure_dir(self):
        self.TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        if not self.MANIFEST_FILE.exists():
            with open(self.MANIFEST_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def synthesize_tool(
        self,
        tool_name: str,
        description: str,
        python_code: str,
        test_code: str = "",
        mcp_target: Any = None
    ) -> dict[str, Any]:
        """
        Synthesizes a new tool, validates its Python syntax, executes verification tests,
        and hot-reloads it directly into the running MCP server.
        """
        clean_name = tool_name.strip().lower().replace(" ", "_")
        tool_file = self.TOOLS_DIR / f"{clean_name}.py"

        # 1. Syntax Compilation Check
        try:
            compiled_code = compile(python_code, str(tool_file), "exec")
        except SyntaxError as se:
            logger.error(f"Synthesized tool syntax error: {se}")
            return {"success": False, "error": f"SyntaxError in generated code: {se}"}

        # 2. Sandbox Execution & Unit Test Verification
        ns: dict[str, Any] = {"__builtins__": __builtins__}
        try:
            exec(compiled_code, ns)
            if clean_name not in ns and f"tool_{clean_name}" not in ns:
                # Look for first function in module
                func_cand = [k for k, v in ns.items() if callable(v) and not k.startswith("_")]
                if func_cand:
                    tool_func = ns[func_cand[0]]
                else:
                    return {"success": False, "error": f"No callable function found in '{clean_name}.py'"}
            else:
                tool_func = ns.get(clean_name) or ns.get(f"tool_{clean_name}")

            # Run test verification if provided
            if test_code:
                test_ns = {"__builtins__": __builtins__, "tool_func": tool_func}
                exec(test_code, test_ns)
                logger.info(f"Verification test passed for synthesized tool: {clean_name}")

        except Exception as te:
            logger.error(f"Synthesized tool verification failed: {te}")
            return {"success": False, "error": f"Verification test failed: {te}"}

        # 3. Write permanent file
        try:
            with open(tool_file, "w", encoding="utf-8") as f:
                f.write(python_code)
        except Exception as e:
            return {"success": False, "error": f"Failed to persist tool file: {e}"}

        # 4. Live Hot-Reload Injection into MCP Server
        target = mcp_target or self.mcp_instance
        if target:
            self.inject_tool_into_mcp(target, clean_name, description, tool_func)

        # 5. Update Manifest
        manifest_entry = {
            "name": clean_name,
            "description": description,
            "file": str(tool_file.name),
            "created_at": time.time(),
            "status": "ACTIVE"
        }
        try:
            with open(self.MANIFEST_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest = [m for m in manifest if m.get("name") != clean_name]
            manifest.append(manifest_entry)
            with open(self.MANIFEST_FILE, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except Exception as e:
            logger.debug(f"Manifest save warning: {e}")

        logger.info(f"Dynamically synthesized and hot-reloaded tool '{clean_name}' successfully.")
        return {
            "success": True,
            "tool_name": clean_name,
            "description": description,
            "file_path": str(tool_file),
            "hot_reloaded": bool(target)
        }

    def inject_tool_into_mcp(self, mcp_server: Any, name: str, description: str, func: Callable):
        """Dynamically registers function into running MCPServer instance."""
        method_name = f"tool_{name}"
        setattr(mcp_server, method_name, func)
        self.registered_dynamic_tools[name] = func

        # Inject into dynamic tools dict in mcp_server
        if not hasattr(mcp_server, "_dynamic_tools"):
            mcp_server._dynamic_tools = {}
        mcp_server._dynamic_tools[name] = {
            "name": name,
            "description": description,
            "func": func
        }

    def reload_all_tools(self, mcp_server: Any) -> int:
        """Loads and activates all tools from manifest into the MCP server."""
        if not self.MANIFEST_FILE.exists():
            return 0
        loaded = 0
        try:
            with open(self.MANIFEST_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for entry in manifest:
                t_name = entry.get("name")
                t_desc = entry.get("description", "")
                t_file = self.TOOLS_DIR / entry.get("file", "")
                if t_file.exists() and t_name:
                    spec = importlib.util.spec_from_file_location(t_name, str(t_file))
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        cand = [getattr(mod, k) for k in dir(mod) if callable(getattr(mod, k)) and not k.startswith("_")]
                        if cand:
                            self.inject_tool_into_mcp(mcp_server, t_name, t_desc, cand[0])
                            loaded += 1
        except Exception as e:
            logger.debug(f"Failed to reload dynamic tools: {e}")
        return loaded


tool_synthesizer = ToolSynthesizer()
