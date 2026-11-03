"""
Unit & Integration Tests for JARVIS REA (Reverse Engineer Anything) Powerup Suite.
Architect: Ansh Tiwari (Chief Systems Architect)

Verifies the full spectrum of REA binary forensics, application deconstruction,
clean-room synthesis, evidence provenance, and MCP tool execution.
"""

import json
import sqlite3
import struct
import zipfile
from pathlib import Path
import pytest

from core.rea_powerup import (
    EvidenceLedger,
    EvidenceType,
    ReverseEngineerAnythingEngine,
    evidence_ledger,
    rea_engine
)
from core.mcp_server import MCPServer
from jarvis_cli import JarvisCLI


# =============================================================================
# 1. Evidence Provenance & Verification Tests
# =============================================================================

def test_evidence_ledger_provenance_and_export():
    ledger = EvidenceLedger()
    
    # 1. Record Observation
    rec_obs = ledger.record(
        target="/bin/app",
        evidence_type=EvidenceType.OBSERVATION,
        summary="Verified PE32+ header and Authenticode certificate table.",
        details={"machine": "x64", "has_sig": True},
        confidence=1.0
    )
    assert rec_obs.evidence_id.startswith("ev_")
    assert rec_obs.confidence == 1.0
    assert rec_obs.evidence_type == EvidenceType.OBSERVATION

    # 2. Record Derivation
    rec_der = ledger.record(
        target="/bin/app",
        evidence_type=EvidenceType.DERIVATION,
        summary="Computed entry point call graph.",
        confidence=0.9
    )
    assert rec_der.confidence == 0.9

    # 3. Filter Records
    obs_list = ledger.filter_records(evidence_type=EvidenceType.OBSERVATION)
    assert len(obs_list) == 1
    assert obs_list[0].evidence_id == rec_obs.evidence_id

    # 4. Export Evidence Bundle
    bundle = ledger.export_bundle()
    assert bundle["total_records"] == 2
    assert "records" in bundle
    assert any(r["evidence_type"] == "observation" for r in bundle["records"])


# =============================================================================
# 2. Native Binary Forensics Tests (PE & ELF)
# =============================================================================

def test_pe_forensics_deep_inspection(tmp_path):
    pe_file = tmp_path / "mock_service.dll"
    
    # Construct a minimal valid PE32+ header in bytes
    e_lfanew = 0x80
    dos_header = bytearray(b"MZ" + b"\x00" * 0x3A)
    dos_header += struct.pack("<I", e_lfanew)
    dos_header += b"\x00" * (e_lfanew - len(dos_header))
    
    # PE Signature: "PE\0\0"
    pe_sig = b"PE\x00\x00"
    # COFF File Header: Machine=x64 (0x8664), NumSections=2, SizeOfOptionalHeader=240
    coff_header = struct.pack("<HHIIIHH", 0x8664, 2, 0, 0, 0, 240, 0x0002)
    # Optional Header PE32+ (Magic=0x20B)
    opt_header = bytearray(struct.pack("<H", 0x020B) + b"\x00" * 238)
    
    # Section Headers (2 sections: .text and .rdata)
    sec_text = struct.pack("<8sIIIIIIHHI", b".text\x00\x00\x00", 0x1000, 0x1000, 0x1000, 0x200, 0, 0, 0, 0, 0x60000020)
    sec_rdata = struct.pack("<8sIIIIIIHHI", b".rdata\x00\x00", 0x1000, 0x2000, 0x1000, 0x1200, 0, 0, 0, 0, 0x40000040)
    
    # Embed an imported DLL name
    payload = b"KERNEL32.dll\x00CreateFileW\x00VirtualAlloc\x00"
    
    full_pe = bytes(dos_header) + pe_sig + coff_header + bytes(opt_header) + sec_text + sec_rdata + payload
    pe_file.write_bytes(full_pe)
    
    res = rea_engine.inspect_pe_details(str(pe_file))
    assert res["success"] is True
    assert "x64" in res["architecture"]
    assert res["pe_format"] == "PE32+"
    assert res["sections_count"] == 2
    assert any(s["name"] == ".text" and s["is_executable"] for s in res["sections"])
    assert "KERNEL32.dll" in res["imported_dlls"]


def test_elf_forensics_deep_inspection(tmp_path):
    elf_file = tmp_path / "mock_daemon"
    
    # Construct minimal valid ELF64 header
    # e_ident: 16 bytes (\x7fELF, class=2 (64-bit), data=1 (little-endian), version=1)
    e_ident = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8
    # e_type=3 (Shared object/PIE), e_machine=62 (x86-64), e_version=1
    elf_hdr = struct.pack("<16sHHIQQQIHHHHHH", e_ident, 3, 62, 1, 0x1000, 64, 0, 0, 64, 56, 1, 64, 0, 0)
    
    payload = b"libc.so.6\x00libm.so.6\x00GNU\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14.text\x00.rodata\x00"
    elf_file.write_bytes(elf_hdr + payload)
    
    res = rea_engine.inspect_elf_details(str(elf_file))
    assert res["success"] is True
    assert res["architecture"] == "x86-64"
    assert res["bitness"] == 64
    assert "libc.so.6" in res["shared_dependencies"]
    assert res["gnu_build_id"] is not None


# =============================================================================
# 3. Modern Language Runtimes (Go, Rust, .NET, Python pyc)
# =============================================================================

def test_go_binary_inspection(tmp_path):
    go_file = tmp_path / "go_service"
    go_content = b"\x7fELF\x02\x01\x01\x00go1.22.4\x00\xfb\xff\xff\xff\x00github.com/org/service/main.main\x00mod\tgithub.com/gorilla/mux\tv1.8.0\n"
    go_file.write_bytes(go_content)
    
    res = rea_engine.inspect_go_binary(str(go_file))
    assert res["success"] is True
    assert res["is_go_binary"] is True
    assert "go1.22.4" in res["go_version"]
    assert res["has_pclntab_table"] is True
    assert any("github.com/gorilla/mux" in m["module"] for m in res["embedded_modules"])
    assert any("main.main" in s for s in res["reconstructed_symbols"])


def test_rust_binary_inspection(tmp_path):
    rust_file = tmp_path / "rust_agent"
    rust_content = b"MZ\x00/rustc/129f3b9964af4d4a709d1383930dda12e7c05f80/src/main.rs:42:10\x00tokio-1.38.0.crate\x00serde-1.0.200.crate\x00_RNvNtCs123_main4init\x00"
    rust_file.write_bytes(rust_content)
    
    res = rea_engine.inspect_rust_binary(str(rust_file))
    assert res["success"] is True
    assert res["is_rust_binary"] is True
    assert res["rustc_commit_hash"] == "129f3b9964af4d4a709d1383930dda12e7c05f80"
    assert any("tokio-1.38.0" in c for c in res["crates_auditable"])
    assert any("_RNvNtCs" in s for s in res["sample_mangled_symbols"])


def test_dotnet_assembly_inspection(tmp_path):
    dotnet_file = tmp_path / "Service.dll"
    # Construct BSJB metadata header
    v_str = b"v4.0.30319\x00\x00"
    bsjb = b"BSJB\x01\x00\x00\x00\x00\x00\x00\x00" + struct.pack("<I", len(v_str)) + v_str
    payload = b"MZ" + b"\x00" * 64 + bsjb + b"\x00System.Net.Http\x00Newtonsoft.Json\x00"
    dotnet_file.write_bytes(payload)
    
    res = rea_engine.inspect_dotnet_assembly(str(dotnet_file))
    assert res["success"] is True
    assert res["is_dotnet_assembly"] is True
    assert "v4.0.30319" in res["clr_runtime_version"]
    assert any("Newtonsoft.Json" in r for r in res["referenced_assemblies"])


def test_python_pyc_inspection(tmp_path):
    pyc_file = tmp_path / "module.pyc"
    # CPython 3.11 magic: 0xa70d0d0a + 12 bytes header + marshal names
    pyc_hdr = b"\xa7\x0d\x0d\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    pyc_content = pyc_hdr + b"\x00def_calculate_metrics\x00api_secret_key\x00"
    pyc_file.write_bytes(pyc_content)
    
    res = rea_engine.inspect_python_pyc(str(pyc_file))
    assert res["success"] is True
    assert res["detected_python_version"] == "Python 3.11"
    assert any("calculate_metrics" in s for s in res["sample_code_symbols"])


# =============================================================================
# 4. Application Forensics (Android APK, SQLite, WebAssembly)
# =============================================================================

def test_android_apk_forensics(tmp_path):
    apk_file = tmp_path / "mobile_app.apk"
    
    # Build ZIP structure simulating an APK
    with zipfile.ZipFile(apk_file, "w") as z:
        manifest_data = b"\x03\x00\x08\x00com.example.enterprise.app\x00android.permission.INTERNET\x00android.permission.ACCESS_FINE_LOCATION\x00.MainActivity\x00"
        z.writestr("AndroidManifest.xml", manifest_data)
        z.writestr("lib/arm64-v8a/libflutter.so", b"ELF...")
        z.writestr("lib/arm64-v8a/libapp.so", b"DartAOT...")
        z.writestr("META-INF/CERT.SF", b"Signature-Version: 1.0\n")
    
    # Append APK Sig Block 42 magic to file bytes
    with open(apk_file, "ab") as f:
        f.write(b"\x00" * 32 + b"APK Sig Block 42")
    
    res = rea_engine.inspect_android_package(str(apk_file))
    assert res["success"] is True
    assert "com.example.enterprise.app" in res["package_name"]
    assert any("permission.INTERNET" in p for p in res["permissions_requested"])
    assert res["signature_schemes"]["v1_jar_signature"] is True
    assert res["signature_schemes"]["v2_v3_apk_signing_block"] is True
    assert res["frameworks"]["is_flutter"] is True
    assert "arm64-v8a" in res["frameworks"]["supported_abis"]


def test_sqlite_database_forensics(tmp_path):
    db_file = tmp_path / "telemetry.db"
    
    # Create valid SQLite database with table and records
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);")
    cursor.execute("INSERT INTO users (name, email) VALUES ('Ansh Tiwari', 'anshtiwarif17@gmail.com');")
    cursor.execute("INSERT INTO users (name, email) VALUES ('Systems Architect', 'architect@jarvis.internal');")
    conn.commit()
    conn.close()
    
    res = rea_engine.inspect_sqlite_database(str(db_file))
    assert res["success"] is True
    assert res["page_size"] >= 512
    assert res["total_entities"] >= 1
    users_tbl = next(e for e in res["entities"] if e["name"] == "users")
    assert users_tbl["row_count"] == 2
    assert "CREATE TABLE users" in users_tbl["sql"]


def test_wasm_binary_inspection(tmp_path):
    wasm_file = tmp_path / "crypto_core.wasm"
    
    # Construct minimal valid WASM binary
    # Magic \0asm + Version 1 + Export Section (ID 7)
    magic = b"\x00asm\x01\x00\x00\x00"
    export_payload = b"\x01\x04hash\x00\x00"  # 1 export named "hash"
    sec_hdr = bytes([7, len(export_payload)])
    wasm_file.write_bytes(magic + sec_hdr + export_payload)
    
    res = rea_engine.inspect_wasm_artifact(str(wasm_file))
    assert res["success"] is True
    assert res["wasm_version"] == 1
    assert any(s["name"] == "Export" for s in res["sections"])
    assert "hash" in res["exported_functions"]
    assert "(export \"hash\" (func $hash))" in res["wat_snippet"]


# =============================================================================
# 5. Clean-Room Synthesis & AgentEnv Generator
# =============================================================================

def test_clean_room_and_agent_env_synthesizer(tmp_path):
    service = "AutonomousTradingGateway"
    endpoints = ["/v1/orders", "/v1/portfolio", "/v1/market/quote"]
    mock_data = {
        "/v1/orders": {"status": "FILLED", "order_id": "ord_9901"},
        "/v1/portfolio": {"nav_usd": 1250000.0, "cash": 50000.0}
    }
    
    # 1. Synthesize AgentEnv
    env_res = rea_engine.synthesize_agent_env(
        service_name=service,
        endpoints=endpoints,
        mock_responses=mock_data,
        workspace_path=str(tmp_path)
    )
    assert env_res["success"] is True
    assert (tmp_path / "mock_server.py").exists()
    assert (tmp_path / "environment_bundle.json").exists()
    
    # Verify environment bundle json
    bundle_data = json.loads((tmp_path / "environment_bundle.json").read_text(encoding="utf-8"))
    assert bundle_data["service_name"] == service
    assert len(bundle_data["endpoints"]) == 3
    
    # 2. Synthesize Clean-Room Client
    client_code = rea_engine.synthesize_clean_room_client(service, endpoints)
    assert f"class {service}Client:" in client_code
    assert "def call_orders" in client_code
    assert "def call_portfolio" in client_code


# =============================================================================
# 6. MCP Server Full REA Tools Integration
# =============================================================================

def test_mcp_server_extended_rea_tools(tmp_path):
    mcp = MCPServer(workspace_path=tmp_path)
    tools = [t["name"] for t in mcp.get_tool_definitions()]
    
    expected_rea_tools = [
        "rea_inspect_binary",
        "rea_unpack_electron",
        "rea_analyze_traffic",
        "rea_clone_client",
        "rea_extract_strings",
        "rea_scan_secrets",
        "rea_inspect_ipc",
        "rea_harvest_routes",
        "rea_audit_security",
        "rea_inspect_pe_details",
        "rea_inspect_elf_details",
        "rea_inspect_go_binary",
        "rea_inspect_rust_binary",
        "rea_inspect_dotnet_assembly",
        "rea_inspect_python_pyc",
        "rea_inspect_android_package",
        "rea_inspect_sqlite_database",
        "rea_inspect_network_capture",
        "rea_inspect_wasm_artifact",
        "rea_synthesize_agent_env",
        "rea_get_evidence_bundle"
    ]
    for et in expected_rea_tools:
        assert et in tools, f"Missing REA tool: {et}"
    
    # Test JSON-RPC invocation of rea_get_evidence_bundle
    rpc_req = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "rea_get_evidence_bundle",
            "arguments": {}
        }
    }
    rpc_res = mcp.handle_jsonrpc(rpc_req)
    assert rpc_res.get("result", {}).get("version") == "6.8.0-jarvis-rea"


# =============================================================================
# 7. Jarvis CLI REA Directives Integration
# =============================================================================

@pytest.mark.asyncio
async def test_jarvis_cli_rea_directives(tmp_path):
    cli = JarvisCLI()
    cli.voice_enabled = False
    
    # 1. REA Help directive
    assert await cli.process_directive("rea help") is True
    assert await cli.process_directive("rea") is True
    
    # 2. REA Secrets directive
    cfg = tmp_path / "prod.env"
    cfg.write_text("API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890\n", encoding="utf-8")
    assert await cli.process_directive(f"rea secrets {cfg}") is True
    
    # 3. REA Evidence Ledger directive
    assert await cli.process_directive("rea evidence") is True

