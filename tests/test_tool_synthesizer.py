"""
Unit & Integration Tests for JARVIS Dynamic Tool Synthesizer & MCP Hot-Reloading
Chief Systems Architect: Ansh Tiwari
"""

import pytest
from core.tool_synthesizer import ToolSynthesizer
from core.mcp_server import MCPServer


def test_tool_synthesis_compilation_and_test_verification(tmp_path):
    """Verifies that a dynamic tool is written, compiled, tested, and persisted."""
    synth = ToolSynthesizer()
    synth.TOOLS_DIR = tmp_path
    synth.MANIFEST_FILE = tmp_path / "manifest.json"
    synth._ensure_dir()

    py_code = """
def custom_math_adder(a: int, b: int) -> int:
    return a + b
"""
    test_code = """
assert tool_func(2, 3) == 5
assert tool_func(10, -5) == 5
"""

    res = synth.synthesize_tool(
        tool_name="custom_math_adder",
        description="Adds two integers dynamically",
        python_code=py_code,
        test_code=test_code
    )

    assert res["success"] is True
    assert res["tool_name"] == "custom_math_adder"
    assert (tmp_path / "custom_math_adder.py").exists()


def test_live_mcp_hot_reloading(tmp_path):
    """Verifies that synthesized tool is injected into live MCPServer without restarting."""
    mcp = MCPServer(workspace_path=tmp_path)
    synth = ToolSynthesizer(mcp_instance=mcp)
    synth.TOOLS_DIR = tmp_path / "dyn_tools"
    synth.MANIFEST_FILE = tmp_path / "dyn_tools" / "manifest.json"
    synth._ensure_dir()

    py_code = """
def greet_creator(name: str = "Master Ansh") -> str:
    return f"Salutations, {name}!"
"""
    test_code = "assert 'Salutations' in tool_func('Ansh')"

    res = synth.synthesize_tool(
        tool_name="greet_creator",
        description="Greets the creator",
        python_code=py_code,
        test_code=test_code,
        mcp_target=mcp
    )

    assert res["success"] is True
    assert res["hot_reloaded"] is True

    # Check live MCP tool definitions
    tools = mcp.get_tool_definitions()
    tool_names = [t["name"] for t in tools]
    assert "greet_creator" in tool_names

    # Call dynamically injected tool directly through MCP JSON-RPC
    rpc_req = {
        "jsonrpc": "2.0",
        "id": 42,
        "method": "tools/call",
        "params": {
            "name": "greet_creator",
            "arguments": {"name": "Chief Architect"}
        }
    }
    rpc_res = mcp.handle_jsonrpc(rpc_req)
    assert rpc_res["result"] == "Salutations, Chief Architect!"


def test_unicode_normalization_in_tool_synthesis(tmp_path):
    """Verifies that non-standard unicode characters like U+2011 non-breaking hyphen and smart quotes are sanitized."""
    synth = ToolSynthesizer()
    synth.TOOLS_DIR = tmp_path
    synth.MANIFEST_FILE = tmp_path / "manifest.json"
    synth._ensure_dir()

    # Code containing non-breaking hyphen \u2011 and curly quotes \u2018 \u2019
    py_code = """
def ping_latency_test(host: str = "localhost") -> dict:
    \"\"\"Latency calculation \u2011 ping verification \u2018fast\u2019\"\"\"
    diff = 100 \u2011 80
    return {"host": host, "ping_ms": diff}
"""
    test_code = """
res = tool_func("127.0.0.1")
assert res[\u2018ping_ms\u2019] == 20
assert res[\u201chost\u201d] == \u2018127.0.0.1\u2019
"""

    res = synth.synthesize_tool(
        tool_name="ping_latency_test",
        description="Measures ping latency",
        python_code=py_code,
        test_code=test_code
    )

    assert res["success"] is True
    assert res["tool_name"] == "ping_latency_test"
    saved_code = (tmp_path / "ping_latency_test.py").read_text(encoding="utf-8")
    assert "\u2011" not in saved_code
    assert "-" in saved_code


