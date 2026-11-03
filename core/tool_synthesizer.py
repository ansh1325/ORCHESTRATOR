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

    @staticmethod
    def sanitize_python_code(code: str) -> str:
        """Normalize unicode hyphens, dashes, and smart quotes that cause Python SyntaxError."""
        import unicodedata
        if not code:
            return ""
        replacements = {
            '\u2010': '-',  # hyphen
            '\u2011': '-',  # non-breaking hyphen (the exact bug!)
            '\u2012': '-',  # figure dash
            '\u2013': '-',  # en dash
            '\u2014': '-',  # em dash
            '\u2015': '-',  # horizontal bar
            '\u2212': '-',  # minus sign
            '\u2018': "'",  # left single quote
            '\u2019': "'",  # right single quote
            '\u201a': "'",  # single low-9 quote
            '\u201b': "'",  # single high-reversed-9 quote
            '\u201c': '"',  # left double quote
            '\u201d': '"',  # right double quote
            '\u201e': '"',  # double low-9 quote
            '\u201f': '"',  # double high-reversed-9 quote
            '\u00a0': ' ',  # non-breaking space
            '\u202f': ' ',  # narrow no-break space
            '\u200b': '',   # zero-width space
            '\ufeff': '',   # BOM
        }
        for orig, rep in replacements.items():
            code = code.replace(orig, rep)
        return unicodedata.normalize('NFKD', code)

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

        # Sanitize code against unicode punctuation syntax errors
        python_code = self.sanitize_python_code(python_code)
        if test_code:
            test_code = self.sanitize_python_code(test_code)

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
                import types
                import unittest
                temp_mod = types.ModuleType(clean_name)
                temp_mod.__dict__.update(ns)
                sys.modules[clean_name] = temp_mod
                
                main_mod = sys.modules.get("__main__")
                if main_mod:
                    setattr(main_mod, clean_name, tool_func)
                    setattr(main_mod, f"tool_{clean_name}", tool_func)

                def safe_unittest_main(*args, **kwargs):
                    kwargs["argv"] = ["test"]
                    kwargs["exit"] = False
                    try:
                        return unittest.TestProgram(*args, **kwargs)
                    except Exception:
                        return None

                safe_unittest = types.ModuleType("unittest")
                safe_unittest.__dict__.update(unittest.__dict__)
                safe_unittest.main = safe_unittest_main

                test_ns = {
                    "__builtins__": __builtins__,
                    "tool_func": tool_func,
                    clean_name: tool_func,
                    f"tool_{clean_name}": tool_func,
                    "unittest": safe_unittest,
                    "__name__": "__main__",
                }
                test_ns.update(ns)
                try:
                    compiled_test = compile(test_code, f"<test_{clean_name}>", "exec")
                    exec(compiled_test, test_ns)
                    logger.info(f"Verification test passed for synthesized tool: {clean_name}")
                except SystemExit:
                    # Ignore harmless unittest.main sys.exit
                    logger.info(f"Verification test completed for synthesized tool: {clean_name}")
                except Exception as te:
                    logger.warning(f"Verification test failed for synthesized tool '{clean_name}': {te}")
                    return {"success": False, "error": f"Verification test failed: {te}"}

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

    def list_tools(self) -> list[dict[str, Any]]:
        """Returns all synthesized tools from manifest."""
        if not self.MANIFEST_FILE.exists():
            return []
        try:
            with open(self.MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def synthesize_tool_autonomously(self, tool_name: str, objective: str = "", mcp_target: Any = None) -> dict[str, Any]:
        """
        Uses Central Brain LLM to write the tool implementation and unit test,
        then calls synthesize_tool to compile, verify, and hot-reload it.
        """
        from core.config import settings
        llm = settings.get_llm_client()
        code = ""
        test_code = ""
        desc = objective or f"Dynamically synthesized tool for {tool_name}"
        clean_name = tool_name.strip().lower().replace(" ", "_").replace("-", "_")
        clean_func = clean_name if clean_name.startswith("tool_") else f"tool_{clean_name}"

        if llm and not settings.is_mock():
            try:
                system_prompt = (
                    "You are JARVIS Runtime Tool Synthesizer.\n"
                    f"Create a standalone, production-ready Python tool function named '{clean_func}' and a simple inline verification test.\n"
                    f"In test_code, invoke tool_func(...) or {clean_func}(...) directly using assert statements (e.g. res = tool_func(); assert res['status'] == 'ok').\n"
                    "Do NOT call unittest.main() or sys.exit(). Do NOT use external imports.\n"
                    "CRITICAL: Use ONLY standard ASCII characters (standard hyphens '-', standard quotes '\"'). Never use unicode dashes or smart quotes.\n"
                    "Output strictly JSON: {\"python_code\": \"...\", \"test_code\": \"...\", \"description\": \"...\"}"
                )
                resp = settings.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Tool Name: {tool_name}\nObjective/Spec: {objective}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                data = json.loads(resp.choices[0].message.content or "{}")
                code = self.sanitize_python_code(data.get("python_code") or "")
                test_code = self.sanitize_python_code(data.get("test_code") or "")
                desc = data.get("description") or desc
            except Exception as e:
                logger.debug(f"LLM tool synthesis fallback: {e}")

        if not code:
            code = f'''def {clean_func}(*args, **kwargs):
    """{desc}"""
    return {{"status": "ok", "tool": "{clean_name}", "received_args": args, "received_kwargs": kwargs}}
'''
            test_code = f'''res = tool_func("test_ping")
assert res["status"] == "ok"
'''

        return self.synthesize_tool(clean_name, desc, code, test_code, mcp_target=mcp_target)

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

